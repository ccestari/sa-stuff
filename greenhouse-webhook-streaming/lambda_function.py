"""
AWS Lambda function to process Greenhouse webhooks
DEPLOYED VERSION - Dec 8, 2025
"""
import json
import base64
from datetime import datetime

def lambda_handler(event, context):
    """Lambda handler for Greenhouse webhook processing"""
    
    # Check if from Firehose or API Gateway
    if 'records' in event:
        return process_firehose_records(event, context)
    else:
        return process_api_gateway_webhook(event, context)

def process_api_gateway_webhook(event, context):
    """Process webhook from API Gateway"""
    try:
        # Parse webhook body - handle None/empty body gracefully
        body_str = event.get('body')
        if body_str is None or body_str == '':
            body_str = '{}'
        body = json.loads(body_str)
        
        # Add metadata
        webhook_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': 'greenhouse_webhook',
            'lambda_request_id': context.aws_request_id,
            'environment': 'production',
            'payload': body
        }
        
        # Log for debugging
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
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }

def process_firehose_records(event, context):
    """Transform Firehose records for Redshift"""
    output_records = []
    
    for record in event['records']:
        try:
            payload = base64.b64decode(record['data']).decode('utf-8')
            data = json.loads(payload)
            transformed_data = json.dumps(data) + '\n'
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
