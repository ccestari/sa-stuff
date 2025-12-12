#!/usr/bin/env python3
"""Update Lambda with retry logic for 500 errors"""
import boto3
import yaml
import json
import zipfile
import io

with open('credentials.yaml') as f:
    creds = yaml.safe_load(f)

with open('config.json') as f:
    config = json.load(f)

prod_creds = creds['production']
session = boto3.Session(
    aws_access_key_id=prod_creds['aws_access_key_id'],
    aws_secret_access_key=prod_creds['aws_secret_access_key'],
    aws_session_token=prod_creds['aws_session_token']
)

lambda_client = session.client('lambda')

# Create improved Lambda code with retry
lambda_code = '''
import json
import boto3
from datetime import datetime

sqs = boto3.client('sqs')
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/309820967897/greenhouse-flattened-records'

def lambda_handler(event, context):
    """Lambda handler with error recovery"""
    
    if 'records' in event:
        return process_firehose_records(event, context)
    else:
        return process_api_gateway_webhook(event, context)

def process_api_gateway_webhook(event, context):
    """Process webhook from API Gateway with retry logic"""
    try:
        body_str = event.get('body')
        if body_str is None or body_str == '':
            body_str = '{}'
        body = json.loads(body_str)
        
        webhook_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': 'greenhouse_webhook',
            'lambda_request_id': context.aws_request_id,
            'environment': 'production',
            'payload': body
        }
        
        # Send to SQS for processing
        try:
            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(webhook_data)
            )
        except Exception as sqs_error:
            print(f"SQS error (will retry): {sqs_error}")
            # Return 500 to trigger Greenhouse retry
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'status': 'error', 'message': 'Temporary failure, will retry'})
            }
        
        print(f"Processed webhook: action={body.get('action')}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'success',
                'message': 'Webhook received',
                'request_id': context.aws_request_id
            })
        }
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        # Return 500 to trigger retry
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }

def process_firehose_records(event, context):
    """Transform Firehose records for Redshift"""
    import base64
    output_records = []
    
    for record in event['records']:
        try:
            payload = base64.b64decode(record['data']).decode('utf-8')
            data = json.loads(payload)
            transformed_data = json.dumps(data) + '\\n'
            encoded_data = base64.b64encode(transformed_data.encode('utf-8')).decode('utf-8')
            
            output_records.append({
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': encoded_data
            })
        except Exception as e:
            print(f"Error transforming record: {e}")
            output_records.append({
                'recordId': record['recordId'],
                'result': 'ProcessingFailed',
                'data': record['data']
            })
    
    return {'records': output_records}
'''

# Create deployment package
print("Creating deployment package...")
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.writestr('lambda_function.py', lambda_code)

zip_buffer.seek(0)

# Update Lambda
print(f"Updating Lambda: {config['lambda']['function_name']}...")
response = lambda_client.update_function_code(
    FunctionName=config['lambda']['function_name'],
    ZipFile=zip_buffer.read()
)

print(f"✅ Lambda updated")
print(f"   Version: {response['Version']}")
print(f"   Last Modified: {response['LastModified']}")
