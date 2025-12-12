#!/usr/bin/env python3
"""Invoke Lambda directly to test - works with any webhook project"""
import boto3
import yaml
import json
import sys

def invoke_lambda(config_path='config.json', credentials_path='credentials.yaml', payload=None):
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

    if not payload:
        payload = {
            'body': json.dumps({
                "test": True,
                "timestamp": "2025-01-01T00:00:00Z"
            })
        }

    print("Invoking Lambda directly...")
    response = lambda_client.invoke(
        FunctionName=config['lambda']['function_name'],
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    result = json.loads(response['Payload'].read())
    print("\nResponse:")
    print(json.dumps(result, indent=2))

    if 'errorMessage' in result:
        print(f"\n❌ Error: {result['errorMessage']}")
        if 'stackTrace' in result:
            print("\nStack trace:")
            for line in result['stackTrace']:
                print(f"  {line}")

if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    creds = sys.argv[2] if len(sys.argv) > 2 else 'credentials.yaml'
    invoke_lambda(config, creds)
