#!/usr/bin/env python3

import boto3
import json
from datetime import datetime, timedelta

def check_schema_mismatch():
    """Check for schema mismatch between transformed data and S3 Tables"""
    
    logs_client = boto3.client('logs')
    s3_client = boto3.client('s3')
    
    print("=== Schema Mismatch Check ===\n")
    
    # 1. Check Firehose logs for delivery errors
    log_group = "/aws/kinesisfirehose/meraki-firehose"
    log_stream = "DestinationDelivery"
    
    try:
        print("1. Checking Firehose delivery logs...")
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(hours=2)).timestamp() * 1000)
        
        response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            startTime=start_time,
            endTime=end_time
        )
        
        events = response.get('events', [])
        if events:
            print(f"   Found {len(events)} log events:")
            for event in events[-5:]:  # Show last 5 events
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message']
                print(f"   [{timestamp}] {message}")
        else:
            print("   No recent log events found")
            
    except Exception as e:
        print(f"   Error reading logs: {e}")
    
    # 2. Check S3 Tables metadata for schema
    try:
        print("\n2. Checking S3 Tables schema from metadata...")
        metadata_location = "s3://e1d195ae-05e5-43b3-b9g3568ba7gyc45rddzmpm7mok79wuse1b--table-s3/metadata/00000-9d1db364-fd35-4893-a3a3-6d3776f6d052.metadata.json"
        
        # Extract bucket and key
        bucket = metadata_location.split('/')[2]
        key = '/'.join(metadata_location.split('/')[3:])
        
        response = s3_client.get_object(Bucket=bucket, Key=key)
        metadata = json.loads(response['Body'].read())
        
        # Extract schema
        if 'schema' in metadata:
            schema = metadata['schema']
            print("   Current S3 Tables schema:")
            for field in schema.get('fields', []):
                field_type = field.get('type', 'unknown')
                if isinstance(field_type, dict):
                    field_type = field_type.get('type', 'complex')
                print(f"   - {field['name']}: {field_type}")
        else:
            print("   No schema found in metadata")
            
    except Exception as e:
        print(f"   Error reading S3 Tables metadata: {e}")
    
    # 3. Show expected transformation output format
    print("\n3. Expected transformation Lambda output format:")
    expected_format = {
        "timestamp": "2025-01-27T22:00:00Z",
        "alert_type": "string", 
        "organization_name": "string",
        "network_name": "string", 
        "device_serial": "string",
        "alert_data": "string (JSON)",
        "raw_payload": "string (full original)"
    }
    
    for field, field_type in expected_format.items():
        print(f"   - {field}: {field_type}")
    
    print("\n4. Troubleshooting steps:")
    print("   - Check if transformation Lambda output matches S3 Tables schema exactly")
    print("   - Verify all required fields are present and non-null")
    print("   - Check data types match (string vs int vs timestamp)")
    print("   - Look for schema evolution issues if types changed")

if __name__ == "__main__":
    check_schema_mismatch()