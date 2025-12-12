#!/usr/bin/env python3
"""
AWS Firehose S3 Tables Delivery Troubleshooting Script
Checks configuration for Firehose delivery to Iceberg S3 Tables
"""

import boto3
import json
from botocore.exceptions import ClientError

def check_firehose_config():
    """Check Firehose delivery stream configuration"""
    firehose = boto3.client('firehose', region_name='us-east-1')
    
    try:
        response = firehose.describe_delivery_stream(
            DeliveryStreamName='meraki-firehose'
        )
        
        stream = response['DeliveryStreamDescription']
        print(f"Firehose Status: {stream['DeliveryStreamStatus']}")
        
        # Check destinations
        destinations = stream['Destinations']
        for i, dest in enumerate(destinations):
            print(f"\nDestination {i+1}:")
            if 'IcebergDestinationDescription' in dest:
                iceberg_dest = dest['IcebergDestinationDescription']
                print(f"  Catalog: {iceberg_dest.get('CatalogConfiguration', {}).get('CatalogArn', 'Not set')}")
                print(f"  Role ARN: {iceberg_dest.get('RoleArn', 'Not set')}")
                print(f"  S3 Config: {iceberg_dest.get('S3Configuration', {}).get('BucketArn', 'Not set')}")
                
                # Check processing configuration
                processing = iceberg_dest.get('ProcessingConfiguration', {})
                print(f"  Processing Enabled: {processing.get('Enabled', False)}")
                if processing.get('Processors'):
                    for proc in processing['Processors']:
                        print(f"    Processor Type: {proc.get('Type')}")
                        for param in proc.get('Parameters', []):
                            if param['ParameterName'] == 'LambdaArn':
                                print(f"    Lambda ARN: {param['ParameterValue']}")
        
        return stream
    except ClientError as e:
        print(f"Error describing Firehose: {e}")
        return None

def check_lambda_permissions():
    """Check Lambda function permissions for Firehose"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        response = lambda_client.get_policy(
            FunctionName='firehose-data-transformation'
        )
        policy = json.loads(response['Policy'])
        
        print("\nLambda Resource Policy:")
        for statement in policy.get('Statement', []):
            if statement.get('Principal', {}).get('Service') == 'firehose.amazonaws.com':
                print(f"  Firehose access: {statement.get('Effect', 'Unknown')}")
                print(f"  Actions: {statement.get('Action', [])}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("\nNo resource policy found for Lambda function")
        else:
            print(f"Error checking Lambda policy: {e}")

def check_iam_role():
    """Check Firehose service role permissions"""
    iam = boto3.client('iam', region_name='us-east-1')
    
    # Get the role ARN from Firehose config first
    firehose = boto3.client('firehose', region_name='us-east-1')
    try:
        response = firehose.describe_delivery_stream(DeliveryStreamName='meraki-firehose')
        destinations = response['DeliveryStreamDescription']['Destinations']
        
        for dest in destinations:
            if 'IcebergDestinationDescription' in dest:
                role_arn = dest['IcebergDestinationDescription'].get('RoleArn')
                if role_arn:
                    role_name = role_arn.split('/')[-1]
                    print(f"\nChecking IAM Role: {role_name}")
                    
                    # Check attached policies
                    try:
                        policies = iam.list_attached_role_policies(RoleName=role_name)
                        print("Attached Policies:")
                        for policy in policies['AttachedPolicies']:
                            print(f"  - {policy['PolicyName']}")
                    except ClientError as e:
                        print(f"Error checking role policies: {e}")
                        
    except ClientError as e:
        print(f"Error getting role info: {e}")

def check_s3_tables_bucket():
    """Check S3 Tables bucket configuration"""
    s3tables = boto3.client('s3tables', region_name='us-east-1')
    
    try:
        response = s3tables.get_table_bucket(
            tableBucketARN='arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki'
        )
        
        print(f"\nS3 Tables Bucket Status: {response.get('name', 'Unknown')}")
        print(f"Creation Date: {response.get('createdAt', 'Unknown')}")
        
    except ClientError as e:
        print(f"Error checking S3 Tables bucket: {e}")

def check_glue_catalog():
    """Check Glue Catalog configuration"""
    glue = boto3.client('glue', region_name='us-east-1')
    
    try:
        # Check if database exists
        response = glue.get_database(
            CatalogId='309820967897',
            Name='s3tablescatalog'
        )
        print(f"\nGlue Database: {response['Database']['Name']}")
        
        # Check table
        try:
            table_response = glue.get_table(
                CatalogId='309820967897',
                DatabaseName='s3tablescatalog',
                Name='lakehouse-meraki'
            )
            table = table_response['Table']
            print(f"Table Location: {table.get('StorageDescriptor', {}).get('Location', 'Not set')}")
            print(f"Table Format: {table.get('Parameters', {}).get('table_type', 'Unknown')}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                print("Table 'lakehouse-meraki' not found in catalog")
            else:
                print(f"Error checking table: {e}")
                
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityNotFoundException':
            print("Database 's3tablescatalog' not found")
        else:
            print(f"Error checking Glue database: {e}")

if __name__ == "__main__":
    print("=== AWS Firehose S3 Tables Delivery Troubleshooting ===\n")
    
    print("1. Checking Firehose Configuration...")
    check_firehose_config()
    
    print("\n2. Checking Lambda Permissions...")
    check_lambda_permissions()
    
    print("\n3. Checking IAM Role...")
    check_iam_role()
    
    print("\n4. Checking S3 Tables Bucket...")
    check_s3_tables_bucket()
    
    print("\n5. Checking Glue Catalog...")
    check_glue_catalog()
    
    print("\n=== Troubleshooting Complete ===")