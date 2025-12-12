#!/usr/bin/env python3
"""Update Lambda function code - works with any webhook project"""
import json
import boto3
import zipfile
import io
import yaml
import sys

def update_lambda(config_path='config.json', credentials_path='credentials.yaml', lambda_file='lambda_function.py'):
    with open(config_path) as f:
        config = json.load(f)

    with open(credentials_path) as f:
        creds = yaml.safe_load(f)

    prod_creds = creds['production']
    session = boto3.Session(
        aws_access_key_id=prod_creds['aws_access_key_id'],
        aws_secret_access_key=prod_creds['aws_secret_access_key'],
        aws_session_token=prod_creds['aws_session_token'],
        region_name=config['aws']['region']
    )

    lambda_client = session.client('lambda')

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(lambda_file, 'lambda_function.py')

    zip_buffer.seek(0)

    print("Updating Lambda function...")
    response = lambda_client.update_function_code(
        FunctionName=config['lambda']['function_name'],
        ZipFile=zip_buffer.read()
    )

    print(f"✅ Updated: {response['FunctionName']}")
    print(f"Version: {response['Version']}")
    print(f"Last Modified: {response['LastModified']}")

if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    creds = sys.argv[2] if len(sys.argv) > 2 else 'credentials.yaml'
    lambda_file = sys.argv[3] if len(sys.argv) > 3 else 'lambda_function.py'
    update_lambda(config, creds, lambda_file)
