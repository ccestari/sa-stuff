#!/usr/bin/env python3
"""
Copy historical Meraki webhook data from nonproduction to production
"""
import json
import boto3
import yaml

def copy_data():
    """Copy historical data from nonprod to prod S3"""
    
    print("=" * 60)
    print("Copying Historical Data: NonProd → Prod")
    print("=" * 60)
    
    # Load credentials
    with open('credentials.yaml') as f:
        creds = yaml.safe_load(f)
    
    # Create sessions
    nonprod_session = boto3.Session(
        aws_access_key_id=creds['nonproduction']['aws_access_key_id'],
        aws_secret_access_key=creds['nonproduction']['aws_secret_access_key'],
        aws_session_token=creds['nonproduction']['aws_session_token']
    )
    
    prod_session = boto3.Session(
        aws_access_key_id=creds['production']['aws_access_key_id'],
        aws_secret_access_key=creds['production']['aws_secret_access_key'],
        aws_session_token=creds['production']['aws_session_token']
    )
    
    nonprod_s3 = nonprod_session.client('s3')
    prod_s3 = prod_session.client('s3')
    
    # Load config
    with open('config.json') as f:
        config = json.load(f)
    
    source_bucket = config['s3']['source_bucket']
    source_prefix = config['s3']['source_prefix']
    dest_bucket = config['s3']['backup_bucket']
    dest_prefix = 'historical/'
    
    print(f"\nSource: s3://{source_bucket}/{source_prefix}")
    print(f"Destination: s3://{dest_bucket}/{dest_prefix}")
    
    # List files
    print("\n1. Listing source files...")
    paginator = nonprod_s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=source_bucket, Prefix=source_prefix)
    
    files = []
    for page in pages:
        if 'Contents' in page:
            files.extend([obj['Key'] for obj in page['Contents'] if obj['Size'] > 0])
    
    print(f"✅ Found {len(files)} files")
    
    # Confirm
    confirm = input(f"\nCopy {len(files)} files to production? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return False
    
    # Copy files
    print("\n2. Copying files...")
    copied = 0
    errors = 0
    
    for i, source_key in enumerate(files):
        try:
            # Get object from nonprod
            response = nonprod_s3.get_object(Bucket=source_bucket, Key=source_key)
            content = response['Body'].read()
            
            # Put to prod
            dest_key = dest_prefix + source_key.replace(source_prefix, '')
            prod_s3.put_object(
                Bucket=dest_bucket,
                Key=dest_key,
                Body=content,
                ContentType='application/json'
            )
            
            copied += 1
            
            if (i + 1) % 10 == 0:
                print(f"   Copied {i + 1}/{len(files)} files")
        
        except Exception as e:
            print(f"   Error copying {source_key}: {e}")
            errors += 1
    
    print("\n" + "=" * 60)
    print("✅ Copy Complete")
    print("=" * 60)
    print(f"Files copied: {copied}/{len(files)}")
    print(f"Errors: {errors}")
    print(f"\nData available at: s3://{dest_bucket}/{dest_prefix}")
    
    return True

if __name__ == "__main__":
    copy_data()
