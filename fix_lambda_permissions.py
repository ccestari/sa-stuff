#!/usr/bin/env python3
"""Add S3 permissions to Lambda role"""
import json
import boto3
import yaml

with open('config.json') as f:
    config = json.load(f)

with open('credentials.yaml') as f:
    creds = yaml.safe_load(f)

prod_creds = creds['production']

session = boto3.Session(
    aws_access_key_id=prod_creds['aws_access_key_id'],
    aws_secret_access_key=prod_creds['aws_secret_access_key'],
    aws_session_token=prod_creds['aws_session_token'],
    region_name=config['aws']['region']
)

iam = session.client('iam')

role_name = config['iam']['lambda_role_name']

s3_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "s3:PutObject",
            "s3:GetObject"
        ],
        "Resource": [
            f"arn:aws:s3:::{config['s3']['raw_bucket']}/*",
            f"arn:aws:s3:::{config['s3']['backup_bucket']}/*"
        ]
    }]
}

print(f"Adding S3 permissions to {role_name}...")
iam.put_role_policy(
    RoleName=role_name,
    PolicyName='S3Access',
    PolicyDocument=json.dumps(s3_policy)
)

print("✅ S3 permissions added")
