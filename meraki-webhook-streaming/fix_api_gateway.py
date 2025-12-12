#!/usr/bin/env python3
"""Fix API Gateway Lambda permission"""
import boto3
import yaml
import json

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
apigateway = session.client('apigateway')

# Get API Gateway ID
apis = apigateway.get_rest_apis()
api_id = None
for api in apis['items']:
    if api['name'] == config['api_gateway']['api_name']:
        api_id = api['id']
        break

if not api_id:
    print("API Gateway not found")
    exit(1)

print(f"API Gateway ID: {api_id}")

# Remove old permission
try:
    lambda_client.remove_permission(
        FunctionName=config['lambda']['function_name'],
        StatementId='apigateway-invoke'
    )
    print("Removed old permission")
except:
    pass

# Add new permission
lambda_client.add_permission(
    FunctionName=config['lambda']['function_name'],
    StatementId='apigateway-invoke',
    Action='lambda:InvokeFunction',
    Principal='apigateway.amazonaws.com',
    SourceArn=f"arn:aws:execute-api:{config['aws']['region']}:{config['aws']['account_id']}:{api_id}/*/*"
)

print("✅ Added Lambda permission for API Gateway")
