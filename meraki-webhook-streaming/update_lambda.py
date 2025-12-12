#!/usr/bin/env python3
"""Update Lambda function with latest code"""
import json
import boto3
import zipfile
import io
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

lambda_client = session.client('lambda')

# Create deployment package
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.write('lambda_function.py', 'lambda_function.py')

zip_buffer.seek(0)

print("Updating Lambda function...")
response = lambda_client.update_function_code(
    FunctionName=config['lambda']['function_name'],
    ZipFile=zip_buffer.read()
)

print(f"✅ Updated: {response['FunctionName']}")
print(f"Version: {response['Version']}")
print(f"Last Modified: {response['LastModified']}")
