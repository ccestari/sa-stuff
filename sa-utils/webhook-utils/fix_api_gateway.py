#!/usr/bin/env python3
"""Fix API Gateway Lambda permission - works with any webhook project"""
import boto3
import yaml
import json
import sys

def fix_api_gateway(config_path='config.json', credentials_path='credentials.yaml'):
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
    apigateway = session.client('apigateway')

    apis = apigateway.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == config['api_gateway']['api_name']:
            api_id = api['id']
            break

    if not api_id:
        print("API Gateway not found")
        return

    print(f"API Gateway ID: {api_id}")

    try:
        lambda_client.remove_permission(
            FunctionName=config['lambda']['function_name'],
            StatementId='apigateway-invoke'
        )
        print("Removed old permission")
    except:
        pass

    lambda_client.add_permission(
        FunctionName=config['lambda']['function_name'],
        StatementId='apigateway-invoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:{config['aws']['region']}:{config['aws']['account_id']}:{api_id}/*/*"
    )

    print("✅ Added Lambda permission for API Gateway")

if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    creds = sys.argv[2] if len(sys.argv) > 2 else 'credentials.yaml'
    fix_api_gateway(config, creds)
