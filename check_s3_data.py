#!/usr/bin/env python3
"""Check S3 bucket for webhook data"""
import boto3
import json
import yaml

def check_s3_data():
    with open('credentials.yaml') as f:
        creds = yaml.safe_load(f)
    
    prod_creds = creds['production']
    session = boto3.Session(
        aws_access_key_id=prod_creds['aws_access_key_id'],
        aws_secret_access_key=prod_creds['aws_secret_access_key'],
        aws_session_token=prod_creds['aws_session_token']
    )
    s3 = session.client('s3')
    
    with open('config.json') as f:
        config = json.load(f)
    
    bucket = config['s3']['backup_bucket']
    print(f"Checking S3 bucket: {bucket}")
    print("=" * 60)
    
    # Check raw webhooks
    print("\nRaw webhooks (raw/):")
    response = s3.list_objects_v2(Bucket=bucket, Prefix='raw/', MaxKeys=10)
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f"  {obj['Key']} ({obj['Size']} bytes)")
    else:
        print("  No raw webhooks found")
    
    # Check firehose backup
    print("\nFirehose backup (firehose-backup/):")
    response = s3.list_objects_v2(Bucket=bucket, Prefix='firehose-backup/', MaxKeys=10)
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f"  {obj['Key']} ({obj['Size']} bytes)")
    else:
        print("  No firehose backups found")

if __name__ == "__main__":
    check_s3_data()
