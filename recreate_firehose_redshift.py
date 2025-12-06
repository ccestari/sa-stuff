#!/usr/bin/env python3
"""
Recreate Firehose with Redshift destination
Deletes existing S3-only stream and creates new one with Redshift loading
"""
import json
import boto3
import time
import yaml

def recreate_firehose():
    with open('config.json') as f:
        config = json.load(f)
    
    with open('credentials.yaml') as f:
        creds = yaml.safe_load(f)
    
    # Use credentials directly from credentials.yaml
    prod_creds = creds['production']
    session = boto3.Session(
        aws_access_key_id=prod_creds['aws_access_key_id'],
        aws_secret_access_key=prod_creds['aws_secret_access_key'],
        aws_session_token=prod_creds['aws_session_token']
    )
    firehose = session.client('firehose')
    iam = session.client('iam')
    
    stream_name = config['firehose']['stream_name']
    
    print("=" * 60)
    print("Recreating Firehose with Redshift Destination")
    print("=" * 60)
    
    # Delete existing stream
    print(f"\n1. Deleting existing stream: {stream_name}")
    try:
        firehose.delete_delivery_stream(DeliveryStreamName=stream_name)
        print("✅ Stream deletion initiated")
        print("   Waiting for deletion to complete (60 seconds)...")
        time.sleep(60)
    except Exception as e:
        if 'ResourceNotFoundException' in str(e):
            print("ℹ️  Stream doesn't exist")
        else:
            print(f"❌ Error: {e}")
            return
    
    # Update Firehose role with Redshift permissions
    print(f"\n2. Updating IAM role permissions")
    role_name = config['iam']['firehose_role_name']
    
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName='FirehoseRedshiftAccess',
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "redshift:DescribeClusters",
                        "redshift:DescribeClusterSubnetGroups"
                    ],
                    "Resource": "*"
                }]
            })
        )
        print("✅ Added Redshift permissions to IAM role")
    except Exception as e:
        print(f"⚠️  Warning: {e}")
    
    # Create new stream with Redshift destination
    print(f"\n3. Creating new Firehose stream with Redshift")
    
    redshift_config = {
        'RoleARN': f"arn:aws:iam::{config['aws']['account_id']}:role/{role_name}",
        'ClusterJDBCURL': f"jdbc:redshift://{config['redshift']['cluster_endpoint']}:{config['redshift']['cluster_port']}/{config['redshift']['database']}",
        'CopyCommand': {
            'DataTableName': f"{config['redshift']['target_schema']}.meraki_webhooks",
            'CopyOptions': "JSON 'auto' TIMEFORMAT 'auto' TRUNCATECOLUMNS BLANKSASNULL EMPTYASNULL"
        },
        'Username': config['redshift']['admin_user'],
        'Password': creds['redshift']['password'],
        'S3BackupMode': 'Disabled',
        'S3Configuration': {
            'RoleARN': f"arn:aws:iam::{config['aws']['account_id']}:role/{role_name}",
            'BucketARN': f"arn:aws:s3:::{config['s3']['backup_bucket']}",
            'BufferingHints': {
                'SizeInMBs': config['firehose']['buffer_size_mb'],
                'IntervalInSeconds': config['firehose']['buffer_interval_seconds']
            },
            'CompressionFormat': 'GZIP'
        },
        'CloudWatchLoggingOptions': {
            'Enabled': True,
            'LogGroupName': f"/aws/kinesisfirehose/{stream_name}",
            'LogStreamName': 'RedshiftDelivery'
        }
    }
    
    try:
        response = firehose.create_delivery_stream(
            DeliveryStreamName=stream_name,
            DeliveryStreamType='DirectPut',
            RedshiftDestinationConfiguration=redshift_config
        )
        print(f"✅ Created Firehose stream: {stream_name}")
        print(f"   ARN: {response['DeliveryStreamARN']}")
        
        print("\n" + "=" * 60)
        print("✅ Firehose Recreated Successfully!")
        print("=" * 60)
        print(f"\nStream: {stream_name}")
        print(f"Destination: Redshift ({config['redshift']['target_schema']}.meraki_webhooks)")
        print(f"Staging: s3://{config['s3']['backup_bucket']}/firehose-staging/")
        print(f"Errors: s3://{config['s3']['backup_bucket']}/firehose-errors/")
        print(f"\nBuffer: {config['firehose']['buffer_size_mb']} MB or {config['firehose']['buffer_interval_seconds']} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating stream: {e}")
        return False

if __name__ == "__main__":
    recreate_firehose()
