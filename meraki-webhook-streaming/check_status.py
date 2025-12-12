#!/usr/bin/env python3
"""
Check status of Meraki webhook streaming infrastructure
"""
import json
import boto3
from setup_credentials import CredentialManager

def check_status():
    """Check status of all infrastructure components"""
    
    print("=" * 60)
    print("Meraki Webhook Streaming - Status Check")
    print("=" * 60)
    
    # Check credentials
    print("\n1. Checking AWS Credentials...")
    cred_manager = CredentialManager()
    if cred_manager.load_credentials() and cred_manager.are_credentials_valid():
        cred_manager.display_status()
    else:
        print("❌ AWS credentials invalid or not found")
        return False
    
    # Get boto3 session
    session = cred_manager.get_boto3_session()
    
    # Load config
    with open('config.json') as f:
        config = json.load(f)
    
    # Check S3 buckets
    print("\n2. Checking S3 Buckets...")
    s3 = session.client('s3')
    
    for bucket_name in [config['s3']['raw_bucket'], config['s3']['backup_bucket']]:
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"✅ {bucket_name}")
        except Exception as e:
            print(f"❌ {bucket_name}: {e}")
    
    # Check Lambda function
    print("\n3. Checking Lambda Function...")
    lambda_client = session.client('lambda')
    
    try:
        response = lambda_client.get_function(
            FunctionName=config['lambda']['function_name']
        )
        print(f"✅ {config['lambda']['function_name']}")
        print(f"   Runtime: {response['Configuration']['Runtime']}")
        print(f"   Memory: {response['Configuration']['MemorySize']} MB")
        print(f"   Timeout: {response['Configuration']['Timeout']} seconds")
        print(f"   Last Modified: {response['Configuration']['LastModified']}")
    except Exception as e:
        print(f"❌ {config['lambda']['function_name']}: {e}")
    
    # Check API Gateway
    print("\n4. Checking API Gateway...")
    try:
        with open('deployment_info.json') as f:
            deployment_info = json.load(f)
            print(f"✅ API URL: {deployment_info['api_url']}")
    except FileNotFoundError:
        print("❌ deployment_info.json not found - run deploy_infrastructure.py")
    
    # Check Firehose
    print("\n5. Checking Firehose Stream...")
    firehose = session.client('firehose')
    
    try:
        response = firehose.describe_delivery_stream(
            DeliveryStreamName=config['firehose']['stream_name']
        )
        status = response['DeliveryStreamDescription']['DeliveryStreamStatus']
        print(f"✅ {config['firehose']['stream_name']}")
        print(f"   Status: {status}")
        
        # Check destinations
        destinations = response['DeliveryStreamDescription']['Destinations']
        if destinations:
            dest = destinations[0]
            if 'ExtendedS3DestinationDescription' in dest:
                s3_dest = dest['ExtendedS3DestinationDescription']
                print(f"   Destination: s3://{s3_dest['BucketARN'].split(':')[-1]}")
    except Exception as e:
        print(f"❌ {config['firehose']['stream_name']}: {e}")
    
    # Check IAM roles
    print("\n6. Checking IAM Roles...")
    iam = session.client('iam')
    
    for role_name in [config['iam']['lambda_role_name'], config['iam']['firehose_role_name']]:
        try:
            iam.get_role(RoleName=role_name)
            print(f"✅ {role_name}")
        except Exception as e:
            print(f"❌ {role_name}: {e}")
    
    print("\n" + "=" * 60)
    print("Status Check Complete")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    check_status()
