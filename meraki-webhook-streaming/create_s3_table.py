#!/usr/bin/env python3
"""
Create S3 Tables bucket and Glue table for Firehose Iceberg delivery
"""

import boto3
import json
from botocore.exceptions import ClientError

def create_s3_tables_bucket():
    """Create S3 Tables bucket if it doesn't exist"""
    s3tables = boto3.client('s3tables', region_name='us-east-1')
    
    try:
        # Check if bucket exists
        response = s3tables.get_table_bucket(
            tableBucketARN='arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki'
        )
        print("S3 Tables bucket already exists")
        return True
    except ClientError as e:
        if 'NotFound' in str(e) or 'NoSuchBucket' in str(e):
            try:
                # Create bucket
                response = s3tables.create_table_bucket(name='lakehouse-meraki')
                print(f"Created S3 Tables bucket: {response['arn']}")
                return True
            except ClientError as create_error:
                print(f"Error creating S3 Tables bucket: {create_error}")
                return False
        else:
            print(f"Error checking S3 Tables bucket: {e}")
            return False

def create_glue_table():
    """Create Glue table for Iceberg format"""
    glue = boto3.client('glue', region_name='us-east-1')
    
    # Basic schema - adjust based on your actual data structure
    table_input = {
        'Name': 'lakehouse-meraki',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'timestamp', 'Type': 'timestamp'},
                {'Name': 'network_id', 'Type': 'string'},
                {'Name': 'device_serial', 'Type': 'string'},
                {'Name': 'data', 'Type': 'string'}
            ],
            'Location': 's3://lakehouse-meraki/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            }
        },
        'Parameters': {
            'table_type': 'ICEBERG',
            'classification': 'iceberg'
        }
    }
    
    try:
        response = glue.create_table(
            CatalogId='309820967897',
            DatabaseName='s3tablescatalog',
            TableInput=table_input
        )
        print("Created Glue table: lakehouse-meraki")
        return True
    except ClientError as e:
        if 'AlreadyExistsException' in str(e):
            print("Glue table already exists")
            return True
        else:
            print(f"Error creating Glue table: {e}")
            return False

def update_iam_role():
    """Add S3 Tables permissions to Firehose IAM role"""
    iam = boto3.client('iam', region_name='us-east-1')
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3tables:PutObject",
                    "s3tables:GetObject",
                    "s3tables:GetBucket",
                    "s3tables:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki",
                    "arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki/*"
                ]
            }
        ]
    }
    
    try:
        # Create inline policy
        response = iam.put_role_policy(
            RoleName='EdnaFirehoseToS3Iceberg',
            PolicyName='S3TablesAccess',
            PolicyDocument=json.dumps(policy_document)
        )
        print("Added S3 Tables permissions to IAM role")
        return True
    except ClientError as e:
        print(f"Error updating IAM role: {e}")
        return False

if __name__ == "__main__":
    print("=== Setting up S3 Tables and Glue configuration ===\n")
    
    success = True
    
    print("1. Creating S3 Tables bucket...")
    if not create_s3_tables_bucket():
        success = False
    
    print("\n2. Creating Glue table...")
    if not create_glue_table():
        success = False
    
    print("\n3. Updating IAM role permissions...")
    if not update_iam_role():
        success = False
    
    if success:
        print("\n✅ Setup complete! Now update Firehose destination configuration in AWS Console.")
        print("\nNext steps:")
        print("1. Go to Kinesis Data Firehose > meraki-firehose")
        print("2. Edit destination configuration")
        print("3. Add destination table: s3tablescatalog.lakehouse-meraki")
        print("4. Set S3 Tables bucket ARN: arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki")
    else:
        print("\n❌ Some steps failed. Check errors above.")