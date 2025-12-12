#!/usr/bin/env python3
"""
Check current status of Firehose delivery and Lambda permissions
"""
import boto3
import json
from datetime import datetime, timedelta

def check_lambda_permissions():
    """Check if Lambda has Firehose permissions"""
    iam = boto3.client('iam')
    role_name = 'edna-meraki-iceberg-load-from-webhook-role-dsx7jtkc'
    
    try:
        # Check for FirehosePermissions policy
        response = iam.get_role_policy(
            RoleName=role_name,
            PolicyName='FirehosePermissions'
        )
        print("✅ Lambda has Firehose permissions policy")
        print(f"Policy: {json.dumps(response['PolicyDocument'], indent=2)}")
        return True
    except iam.exceptions.NoSuchEntityException:
        print("❌ Lambda missing Firehose permissions policy")
        return False

def check_firehose_metrics():
    """Check Firehose delivery metrics"""
    cloudwatch = boto3.client('cloudwatch')
    
    # Check last 1 hour
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    metrics = [
        'IncomingRecords',
        'DeliveryToS3.Records',
        'DeliveryToS3Tables.Records'
    ]
    
    for metric in metrics:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Kinesis/Firehose',
                MetricName=metric,
                Dimensions=[
                    {'Name': 'DeliveryStreamName', 'Value': 'meraki-firehose'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            total = sum(point['Sum'] for point in response['Datapoints'])
            print(f"{metric}: {total}")
        except Exception as e:
            print(f"Error getting {metric}: {e}")

def check_lambda_metrics():
    """Check Lambda invocation metrics"""
    cloudwatch = boto3.client('cloudwatch')
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    metrics = ['Invocations', 'Errors']
    
    for metric in metrics:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName=metric,
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': 'edna-meraki-iceberg-load-from-webhook'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            total = sum(point['Sum'] for point in response['Datapoints'])
            print(f"Lambda {metric}: {total}")
        except Exception as e:
            print(f"Error getting Lambda {metric}: {e}")

def add_firehose_permissions():
    """Add Firehose permissions to Lambda role"""
    iam = boto3.client('iam')
    role_name = 'edna-meraki-iceberg-load-from-webhook-role-dsx7jtkc'
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "firehose:PutRecord",
                    "firehose:PutRecordBatch"
                ],
                "Resource": "arn:aws:firehose:us-east-1:309820967897:deliverystream/meraki-firehose"
            }
        ]
    }
    
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName='FirehosePermissions',
            PolicyDocument=json.dumps(policy_document)
        )
        print("✅ Added Firehose permissions to Lambda role")
        return True
    except Exception as e:
        print(f"❌ Error adding permissions: {e}")
        return False

if __name__ == "__main__":
    print("=== Checking Firehose Delivery Status ===")
    
    # Check Lambda permissions
    print("\n1. Lambda Permissions:")
    has_permissions = check_lambda_permissions()
    
    if not has_permissions:
        print("\n🔧 Adding Firehose permissions...")
        add_firehose_permissions()
    
    # Check metrics
    print("\n2. Firehose Metrics (last hour):")
    check_firehose_metrics()
    
    print("\n3. Lambda Metrics (last hour):")
    check_lambda_metrics()
    
    print("\n=== Next Steps ===")
    if not has_permissions:
        print("- Firehose permissions were missing and have been added")
        print("- Try triggering the webhook again")
    else:
        print("- Permissions look correct")
        print("- Check Lambda logs for any errors")
        print("- Verify webhook is sending data to correct Lambda")