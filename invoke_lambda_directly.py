#!/usr/bin/env python3
"""Invoke Lambda directly to see error"""
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

test_event = {
    'body': json.dumps({
        "version": "0.1",
        "organizationId": "25998",
        "networkId": "L_123",
        "deviceSerial": "Q3CA-TEST",
        "deviceName": "Test Device",
        "alertType": "Sensor change detected",
        "alertId": "123",
        "alertLevel": "informational",
        "occurredAt": "2025-12-05T23:00:00Z"
    })
}

print("Invoking Lambda directly...")
response = lambda_client.invoke(
    FunctionName=config['lambda']['function_name'],
    InvocationType='RequestResponse',
    Payload=json.dumps(test_event)
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
