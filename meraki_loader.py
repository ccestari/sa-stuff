import json
import boto3
import logging
import os
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to receive Meraki webhooks and forward to Firehose
    """
    
    # Initialize Firehose client
    firehose = boto3.client('firehose')
    
    try:
        # Log the incoming event for debugging
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract the webhook payload
        if 'body' in event:
            # If coming from API Gateway, the body might be a string
            if isinstance(event['body'], str):
                webhook_data = json.loads(event['body'])
            else:
                webhook_data = event['body']
        else:
            webhook_data = event
        
        # Add metadata to the payload
        enriched_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'meraki-webhook',
            'lambda_request_id': context.aws_request_id,
            'environment': 'non-prod',
            'payload': webhook_data
        }
        
        # Convert to JSON string with newline (required by Firehose)
        firehose_record = json.dumps(enriched_data) + '\n'
        
        # Check if FIREHOSE_STREAM_NAME environment variable is set
        firehose_stream_name = os.environ.get('FIREHOSE_STREAM_NAME')
        #firehose_stream_name = 'meraki-webhooks-to-s3-iceberg'

        if firehose_stream_name:
            # Send data to Firehose - original
            try:
                response = firehose.put_record(
                    # Commenting out and hard coding for testing - error thrown on DeliveryStreamName not conforming to naming convention
                    #DeliveryStreamName = firehose_stream_name,
                    DeliveryStreamName = 'meraki-webhooks-to-s3-iceberg',
                    Record={
                        'Data': firehose_record
                    }
                )
                
                logger.info(f"Successfully sent data to Firehose. Record ID: {response['RecordId']}")
                
                # Return success response
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'message': 'Webhook processed and sent to Firehose successfully',
                        'environment': 'non-prod',
                        'firehose_record_id': response['RecordId'],
                        'firehose_stream': firehose_stream_name
                    })
                }

            except Exception as firehose_error:
                logger.error(f"Error sending to Firehose: {str(firehose_error)}")
                # Continue to logging mode if Firehose fails
        
        # Log mode - when no Firehose stream is configured or Firehose fails
        #logger.info(f"WEBHOOK DATA (no Firehose configured): {firehose_record}")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Webhook received and logged successfully (no Firehose configured)',
                'environment': 'non-prod',
                'logged_data': enriched_data
            })
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid JSON payload', 'environment': 'non-prod'})
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error', 'environment': 'non-prod'})
        }
