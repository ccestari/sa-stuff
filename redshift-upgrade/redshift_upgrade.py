#!/usr/bin/env python3
"""Redshift Cluster Major Version Upgrade Script"""
import boto3
import yaml
import json
from datetime import datetime

def create_snapshot(client, cluster_id):
    """Create manual snapshot before upgrade"""
    snapshot_id = f"{cluster_id}-upgrade-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"📸 Creating snapshot: {snapshot_id}")
    
    client.create_cluster_snapshot(
        SnapshotIdentifier=snapshot_id,
        ClusterIdentifier=cluster_id,
        Tags=[{'Key': 'Purpose', 'Value': 'Pre-upgrade backup'}]
    )
    
    print("⏳ Waiting for snapshot to complete...")
    waiter = client.get_waiter('snapshot_available')
    waiter.wait(SnapshotIdentifier=snapshot_id)
    print(f"✅ Snapshot created: {snapshot_id}")
    return snapshot_id

def get_next_major_version(current_version):
    """Calculate next major version"""
    parts = current_version.split('.')
    major = int(parts[0])
    return f"{major + 1}.0"

def upgrade_cluster(client, cluster_id, target_version):
    """Upgrade cluster to target version"""
    print(f"🔄 Upgrading to version {target_version}...")
    
    client.modify_cluster(
        ClusterIdentifier=cluster_id,
        ClusterVersion=target_version,
        AllowVersionUpgrade=True
    )
    
    print("⏳ Upgrade in progress (30-60 minutes)...")
    waiter = client.get_waiter('cluster_available')
    waiter.wait(ClusterIdentifier=cluster_id, WaiterConfig={'Delay': 60, 'MaxAttempts': 60})
    print(f"✅ Upgrade complete to version {target_version}")

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
    
    client = session.client('redshift')
    
    response = client.describe_clusters(ClusterIdentifier=cluster_id)
    cluster = response['Clusters'][0]
    current_version = cluster['ClusterVersion']
    status = cluster['ClusterStatus']
    
    print(f"📊 Cluster: {cluster_id}")
    print(f"   Current version: {current_version}")
    print(f"   Status: {status}")
    
    if status != 'available':
        print(f"❌ Cluster must be 'available'. Current: {status}")
        return
    
    next_version = get_next_major_version(current_version)
    print(f"\n🎯 Target version: {next_version}")
    
    confirm = input(f"\nProceed with upgrade {current_version} → {next_version}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    snapshot_id = create_snapshot(client, cluster_id)
    upgrade_cluster(client, cluster_id, next_version)
    
    response = client.describe_clusters(ClusterIdentifier=cluster_id)
    final_version = response['Clusters'][0]['ClusterVersion']
    
    print(f"\n✅ Upgrade complete!")
    print(f"   Previous: {current_version}")
    print(f"   Current: {final_version}")
    print(f"   Snapshot: {snapshot_id}")
    print(f"\n💡 Monitor for 24 hours before next upgrade")

if __name__ == "__main__":
    main()
