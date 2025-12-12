#!/usr/bin/env python3
"""
CloudWatch utility functions for metrics and monitoring
"""
import boto3
from datetime import datetime, timedelta


def get_lambda_metrics(function_name, hours=1):
    """Get Lambda invocation and error metrics"""
    cloudwatch = boto3.client('cloudwatch')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    metrics = ['Invocations', 'Errors', 'Duration', 'Throttles']
    results = {}
    
    for metric in metrics:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName=metric,
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum'] if metric in ['Invocations', 'Errors', 'Throttles'] else ['Average']
            )
            
            if response['Datapoints']:
                stat = 'Sum' if metric in ['Invocations', 'Errors', 'Throttles'] else 'Average'
                total = sum(point[stat] for point in response['Datapoints'])
                results[metric] = total
            else:
                results[metric] = 0
        except:
            results[metric] = 0
    
    return results
