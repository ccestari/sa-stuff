"""
AWS Lambda function to process Meraki webhooks
Handles varying payload structures and delivers to S3 and Firehose
"""
import json
import base64
import boto3
import os
from datetime import datetime

def detect_schema_version(payload):
    """Detect schema version based on field presence"""
    if 'version' in payload and payload.get('version') == '0.1':
        return 'v0.1'
    required_fields = ['organizationId', 'networkId', 'deviceSerial', 'alertType']
    if all(field in payload for field in required_fields):
        return 'v0.1'
    return 'unknown'

def alert_unknown_schema(payload):
    """Alert on unknown schema via CloudWatch Logs and SNS"""
    print(f"⚠️ UNKNOWN SCHEMA DETECTED: {json.dumps(payload, indent=2)}")
    sns_topic = os.environ.get('ALERT_SNS_TOPIC')
    if sns_topic:
        try:
            sns = boto3.client('sns')
            sns.publish(
                TopicArn=sns_topic,
                Subject='Meraki Webhook: Unknown Schema Detected',
                Message=f"Unknown schema detected:\n\n{json.dumps(payload, indent=2)}"
            )
        except Exception as e:
            print(f"Failed to send SNS alert: {e}")

def alert_processing_error(payload, error_msg):
    """Alert on processing errors"""
    print(f"❌ PROCESSING ERROR: {error_msg}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    sns_topic = os.environ.get('ALERT_SNS_TOPIC')
    if sns_topic:
        try:
            sns = boto3.client('sns')
            sns.publish(
                TopicArn=sns_topic,
                Subject='Meraki Webhook: Processing Error',
                Message=f"Error: {error_msg}\n\nPayload: {json.dumps(payload, indent=2)}"
            )
        except Exception as e:
            print(f"Failed to send SNS alert: {e}")

def flatten_meraki_payload(payload):
    """
    Flatten Meraki webhook payload to consistent schema
    Handles varying alert types and structures
    """
    try:
        schema_version = detect_schema_version(payload)
        if schema_version == 'unknown':
            alert_unknown_schema(payload)
        
        # Base fields present in all webhooks
        flattened = {
            'version': payload.get('version'),
            'shared_secret': payload.get('sharedSecret'),
            'sent_at': payload.get('sentAt'),
            'organization_id': payload.get('organizationId'),
            'organization_name': payload.get('organizationName'),
            'organization_url': payload.get('organizationUrl'),
            'network_id': payload.get('networkId'),
            'network_name': payload.get('networkName'),
            'network_url': payload.get('networkUrl'),
            'network_tags': json.dumps(payload.get('networkTags', [])),
            'device_serial': payload.get('deviceSerial'),
            'device_mac': payload.get('deviceMac'),
            'device_name': payload.get('deviceName'),
            'device_url': payload.get('deviceUrl'),
            'device_tags': json.dumps(payload.get('deviceTags', [])),
            'device_model': payload.get('deviceModel'),
            'alert_id': payload.get('alertId'),
            'alert_type': payload.get('alertType'),
            'alert_type_id': payload.get('alertTypeId'),
            'alert_level': payload.get('alertLevel'),
            'occurred_at': payload.get('occurredAt')
        }
        
        # Alert data - varies by alert type
        alert_data = payload.get('alertData', {})
        if alert_data:
            flattened['alert_config_id'] = alert_data.get('alertConfigId')
            flattened['alert_config_name'] = alert_data.get('alertConfigName')
            flattened['started_alerting'] = alert_data.get('startedAlerting')
            
            # Trigger data - can be array
            trigger_data = alert_data.get('triggerData', [])
            if trigger_data and len(trigger_data) > 0:
                first_trigger = trigger_data[0]
                flattened['condition_id'] = first_trigger.get('conditionId')
                
                trigger = first_trigger.get('trigger', {})
                flattened['trigger_ts'] = trigger.get('ts')
                flattened['trigger_type'] = trigger.get('type')
                flattened['trigger_node_id'] = trigger.get('nodeId')
                flattened['trigger_sensor_value'] = trigger.get('sensorValue')
        
        return flattened
        
    except Exception as e:
        print(f"Error flattening payload: {e}")
        alert_processing_error(payload, str(e))
        return {}

def lambda_handler(event, context):
    """
    Lambda handler for Meraki webhook processing
    
    For API Gateway: Receives webhook, stores raw to S3, sends to Firehose
    For Firehose: Transforms records for Redshift COPY
    """
    
    # Check if this is from Firehose (transformation) or API Gateway (webhook)
    if 'records' in event:
        # Firehose transformation
        return process_firehose_records(event, context)
    else:
        # API Gateway webhook
        return process_api_gateway_webhook(event, context)

def process_api_gateway_webhook(event, context):
    """Process webhook from API Gateway"""
    try:
        s3_client = boto3.client('s3')
        redshift_data = boto3.client('redshift-data')
        
        # Parse webhook body
        body = json.loads(event.get('body', '{}'))
        
        # Add metadata
        webhook_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': 'meraki_webhook',
            'lambda_request_id': context.aws_request_id,
            'environment': 'production',
            'payload': body
        }
        
        # Flatten the payload for Redshift
        flattened_data = flatten_meraki_payload(body)
        webhook_data.update(flattened_data)
        
        # Store raw payload to S3
        try:
            raw_bucket = os.environ.get('RAW_BUCKET', 'edna-stream-meraki')
            timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
            s3_key = f"raw/{timestamp}-{context.aws_request_id}.json"
            
            s3_client.put_object(
                Bucket=raw_bucket,
                Key=s3_key,
                Body=json.dumps(body, indent=2),
                ContentType='application/json'
            )
            webhook_data['s3_raw_location'] = f"s3://{raw_bucket}/{s3_key}"
        except Exception as s3_error:
            print(f"S3 raw storage error: {s3_error}")
        
        # Write to S3 for Redshift COPY JOB (date-partitioned, newline-delimited JSON)
        try:
            copy_bucket = os.environ.get('RAW_BUCKET', 'edna-stream-meraki')
            now = datetime.utcnow()
            date_partition = now.strftime('%Y/%m/%d')
            hour_partition = now.strftime('%H')
            s3_key = f"copy-job/{date_partition}/{hour_partition}/{context.aws_request_id}.json"
            
            s3_client.put_object(
                Bucket=copy_bucket,
                Key=s3_key,
                Body=json.dumps(webhook_data) + '\n',
                ContentType='application/json'
            )
            print(f"✅ S3 COPY JOB: s3://{copy_bucket}/{s3_key}")
        except Exception as copy_error:
            print(f"❌ S3 COPY JOB ERROR: {copy_error}")
            raise
        
        # Log for debugging
        print(f"Processed webhook: alert_type={body.get('alertType')}, "
              f"device={flattened_data.get('device_name')}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'status': 'success',
                'message': 'Webhook received and processed',
                'request_id': context.aws_request_id
            })
        }
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
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
            # Decode the data
            payload = base64.b64decode(record['data']).decode('utf-8')
            data = json.loads(payload)
            
            # Transform for Redshift - create a flattened JSON string
            transformed_data = json.dumps(data) + '\n'
            
            # Encode back to base64
            encoded_data = base64.b64encode(transformed_data.encode('utf-8')).decode('utf-8')
            
            output_records.append({
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': encoded_data
            })
            
        except Exception as e:
            print(f"Error transforming record {record['recordId']}: {e}")
            # Mark as failed
            output_records.append({
                'recordId': record['recordId'],
                'result': 'ProcessingFailed',
                'data': record['data']
            })
    
    return {
        'records': output_records
    }

# For local testing
if __name__ == '__main__':
    # Test with sample Meraki webhook
    test_event = {
        'body': json.dumps({
            "version": "0.1",
            "sharedSecret": "test123",
            "sentAt": "2025-01-15T12:00:00Z",
            "organizationId": "25998",
            "organizationName": "Success Charter Network",
            "networkId": "L_123456",
            "networkName": "Test Network",
            "deviceSerial": "Q3CA-TEST-1234",
            "deviceMac": "bc:33:40:ff:c9:e7",
            "deviceName": "Test Device",
            "deviceModel": "MT10",
            "alertId": "123456",
            "alertType": "Sensor change detected",
            "alertTypeId": "sensor_alert",
            "alertLevel": "informational",
            "occurredAt": "2025-01-15T11:59:00Z",
            "alertData": {
                "alertConfigId": 789,
                "alertConfigName": "Temperature Threshold",
                "triggerData": [{
                    "conditionId": 456,
                    "trigger": {
                        "ts": 1705320000.0,
                        "type": "temperature",
                        "nodeId": 123,
                        "sensorValue": 18.5
                    }
                }],
                "startedAlerting": True
            }
        })
    }
    
    class MockContext:
        request_id = 'test-request-id'
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))
