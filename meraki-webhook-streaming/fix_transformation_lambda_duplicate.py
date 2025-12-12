#!/usr/bin/env python3

import json
import base64
import gzip
import polars as pl
from datetime import datetime

def lambda_handler(event, context):
    """Fixed transformation Lambda that handles duplicate column names"""
    
    output = []
    
    for record in event['records']:
        try:
            # Decode the data
            payload = base64.b64decode(record['data'])
            
            # Handle gzip compression if present
            try:
                payload = gzip.decompress(payload)
            except:
                pass  # Not compressed
            
            # Parse JSON
            data = json.loads(payload.decode('utf-8'))
            
            # Extract fields safely to avoid duplicate column names
            timestamp = data.get('timestamp', datetime.utcnow().isoformat())
            source = data.get('source', 'unknown')
            lambda_request_id = data.get('lambda_request_id', '')
            environment = data.get('environment', 'unknown')
            
            payload_data = data.get('payload', {})
            alert_data = payload_data.get('alertData', {})
            
            # Create transformed record with unique column names
            transformed_record = {
                'timestamp': timestamp,
                'alert_type': alert_data.get('alertType', ''),
                'organization_name': payload_data.get('organizationName', ''),
                'network_name': payload_data.get('networkName', ''),
                'device_serial': payload_data.get('deviceSerial', ''),  # Use root level deviceSerial
                'alert_data': json.dumps(alert_data),
                'raw_payload': json.dumps(data)
            }
            
            # Convert to JSON string for Firehose
            output_data = json.dumps(transformed_record) + '\n'
            
            output.append({
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(output_data.encode('utf-8')).decode('utf-8')
            })
            
        except Exception as e:
            print(f"Error processing record {record['recordId']}: {str(e)}")
            # Return processing failure
            output.append({
                'recordId': record['recordId'],
                'result': 'ProcessingFailed'
            })
    
    print(f"Successfully processed {len([r for r in output if r['result'] == 'Ok'])} records")
    return {'records': output}

# Test the function locally if needed
if __name__ == "__main__":
    # Test with sample data
    test_event = {
        'records': [{
            'recordId': 'test-record-1',
            'data': base64.b64encode(json.dumps({
                "timestamp": "2025-01-27T22:20:26.807511",
                "source": "meraki-webhook",
                "lambda_request_id": "test-123",
                "environment": "non-prod",
                "payload": {
                    "alertData": {
                        "alertType": "settings_changed",
                        "deviceSerial": "Q2XX-XXXX-XXXX",
                        "deviceName": "Test Device"
                    },
                    "organizationName": "Test Organization",
                    "networkName": "Test Network",
                    "deviceSerial": "Q2XX-XXXX-XXXX"
                }
            }).encode('utf-8')).decode('utf-8')
        }]
    }
    
    result = lambda_handler(test_event, None)
    print("Test result:", result)