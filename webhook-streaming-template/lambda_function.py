"""
AWS Lambda function template for webhook streaming to Redshift
Handles API Gateway webhooks and Firehose transformations
"""
import json
import boto3
import os
from datetime import datetime
from sa_utils.aws_utilities import (
    parse_webhook_body,
    add_webhook_metadata,
    create_api_gateway_response,
    process_firehose_records
)


def lambda_handler(event, context):
    """Main Lambda handler - routes to API Gateway or Firehose processor"""
    if 'records' in event:
        return process_firehose_records(event['records'])
    else:
        return process_webhook(event, context)


def process_webhook(event, context):
    """Process webhook from API Gateway"""
    try:
        body = parse_webhook_body(event)
        
        # Add metadata
        webhook_data = add_webhook_metadata(
            body, 
            context, 
            source=os.environ.get('WEBHOOK_SOURCE', 'webhook'),
            environment=os.environ.get('ENVIRONMENT', 'production')
        )
        
        # Store raw to S3
        store_to_s3(body, context)
        
        # Send to Firehose (optional)
        send_to_firehose(webhook_data)
        
        print(f"Processed webhook: {body.get('action') or body.get('alertType')}")
        
        return create_api_gateway_response(200, {
            'status': 'success',
            'message': 'Webhook received',
            'request_id': context.aws_request_id
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return create_api_gateway_response(500, {
            'status': 'error',
            'message': str(e)
        })


def store_to_s3(payload, context):
    """Store raw payload to S3"""
    bucket = os.environ.get('RAW_BUCKET')
    if not bucket:
        return
    
    try:
        s3 = boto3.client('s3')
        timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
        key = f"raw/{timestamp}-{context.aws_request_id}.json"
        
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(payload, indent=2),
            ContentType='application/json'
        )
    except Exception as e:
        print(f"S3 error: {e}")


def send_to_firehose(data):
    """Send data to Firehose stream"""
    stream = os.environ.get('FIREHOSE_STREAM')
    if not stream:
        return
    
    try:
        firehose = boto3.client('firehose')
        firehose.put_record(
            DeliveryStreamName=stream,
            Record={'Data': json.dumps(data) + '\n'}
        )
    except Exception as e:
        print(f"Firehose error: {e}")
