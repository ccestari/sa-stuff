#!/usr/bin/env python3
"""
Firehose utility functions for monitoring and troubleshooting
"""
import boto3
import json
from datetime import datetime, timedelta


def check_firehose_metrics(stream_name, hours=1):
    """Check Firehose delivery metrics"""
    cloudwatch = boto3.client('cloudwatch')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    metrics = {
        'IncomingRecords': 'Records received',
        'DeliveryToS3.Records': 'Delivered to S3',
        'DeliveryToS3Tables.Records': 'Delivered to S3 Tables',
        'DeliveryToIceberg.Records': 'Delivered to Iceberg'
    }
    
    results = {}
    for metric, description in metrics.items():
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Kinesis/Firehose',
                MetricName=metric,
                Dimensions=[{'Name': 'DeliveryStreamName', 'Value': stream_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            total = sum(point['Sum'] for point in response['Datapoints'])
            results[metric] = {'value': total, 'description': description}
        except:
            results[metric] = {'value': 0, 'description': description}
    
    return results


def add_firehose_permissions_to_lambda(role_name, firehose_arn):
    """Add Firehose permissions to Lambda IAM role"""
    iam = boto3.client('iam')
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["firehose:PutRecord", "firehose:PutRecordBatch"],
            "Resource": firehose_arn
        }]
    }
    
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='FirehosePermissions',
        PolicyDocument=json.dumps(policy_document)
    )
