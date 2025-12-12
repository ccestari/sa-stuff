#!/usr/bin/env python3
"""Redshift Cluster Activity Monitor"""
import boto3
import yaml
import json
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_query_patterns(cloudwatch, cluster_id, days=7):
    """Analyze query patterns over the past N days"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    print(f"📊 Analyzing query patterns from {start_time.date()} to {end_time.date()}...")
    
    metrics = ['DatabaseConnections', 'CPUUtilization', 'NetworkReceiveThroughput']
    hourly_stats = defaultdict(lambda: {'connections': [], 'cpu': [], 'network': []})
    
    for metric_name in metrics:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName=metric_name,
            Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average']
        )
        
        for datapoint in response['Datapoints']:
            hour = datapoint['Timestamp'].hour
            if metric_name == 'DatabaseConnections':
                hourly_stats[hour]['connections'].append(datapoint['Average'])
            elif metric_name == 'CPUUtilization':
                hourly_stats[hour]['cpu'].append(datapoint['Average'])
            elif metric_name == 'NetworkReceiveThroughput':
                hourly_stats[hour]['network'].append(datapoint['Average'])
    
    print("\n⏰ Average Activity by Hour (UTC):")
    print(f"{'Hour':<6} {'Connections':<15} {'CPU %':<10} {'Network MB/s':<15} {'Recommendation'}")
    print("-" * 70)
    
    low_activity_hours = []
    for hour in range(24):
        if hour in hourly_stats:
            avg_conn = sum(hourly_stats[hour]['connections']) / len(hourly_stats[hour]['connections'])
            avg_cpu = sum(hourly_stats[hour]['cpu']) / len(hourly_stats[hour]['cpu'])
            avg_network = sum(hourly_stats[hour]['network']) / len(hourly_stats[hour]['network']) / 1024 / 1024
            
            is_low = avg_conn < 5 and avg_cpu < 20
            recommendation = "✅ Good window" if is_low else ""
            
            print(f"{hour:02d}:00  {avg_conn:>6.1f}          {avg_cpu:>6.1f}     {avg_network:>8.2f}        {recommendation}")
            
            if is_low:
                low_activity_hours.append(hour)
    
    print(f"\n💡 Recommended maintenance windows (UTC):")
    if low_activity_hours:
        for hour in low_activity_hours:
            print(f"   {hour:02d}:00 - {(hour+1)%24:02d}:00")
    else:
        print("   No clear low-activity periods found. Consider weekends.")

def main():
    with open('config.json') as f:
        config = json.load(f)
    
    with open('credentials.yaml') as f:
        creds = yaml.safe_load(f)
    
    prod_creds = creds['production']
    cluster_id = config['redshift']['cluster_identifier']
    region = config['aws']['region']
    
    session = boto3.Session(
        aws_access_key_id=prod_creds['aws_access_key_id'],
        aws_secret_access_key=prod_creds['aws_secret_access_key'],
        aws_session_token=prod_creds['aws_session_token'],
        region_name=region
    )
    
    redshift = session.client('redshift')
    cloudwatch = session.client('cloudwatch')
    
    print(f"🔍 Checking cluster: {cluster_id}")
    response = redshift.describe_clusters(ClusterIdentifier=cluster_id)
    cluster = response['Clusters'][0]
    print(f"   Version: {cluster['ClusterVersion']}")
    print(f"   Status: {cluster['ClusterStatus']}")
    print(f"   Current maintenance window: {cluster.get('PreferredMaintenanceWindow', 'Not set')}\n")
    
    analyze_query_patterns(cloudwatch, cluster_id, days=7)

if __name__ == "__main__":
    main()
