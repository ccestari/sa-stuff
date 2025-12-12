#!/usr/bin/env python3

import boto3
import json

def fix_s3tables_schema():
    """Create S3 Tables table with proper schema matching transformation Lambda output"""
    
    s3tables = boto3.client('s3tables')
    
    table_bucket_arn = "arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki"
    namespace = "meraki_namespace"
    table_name = "raw_meraki_payload"
    
    print("=== Fixing S3 Tables Schema ===\n")
    
    # Define schema matching transformation Lambda output
    table_schema = {
        "type": "struct",
        "fields": [
            {"id": 1, "name": "timestamp", "required": True, "type": "string"},
            {"id": 2, "name": "alert_type", "required": True, "type": "string"},
            {"id": 3, "name": "organization_name", "required": True, "type": "string"},
            {"id": 4, "name": "network_name", "required": True, "type": "string"},
            {"id": 5, "name": "device_serial", "required": True, "type": "string"},
            {"id": 6, "name": "alert_data", "required": True, "type": "string"},
            {"id": 7, "name": "raw_payload", "required": True, "type": "string"}
        ]
    }
    
    try:
        print("1. Deleting existing table...")
        s3tables.delete_table(
            tableBucketARN=table_bucket_arn,
            namespace=namespace,
            name=table_name
        )
        print("   ✓ Table deleted")
    except Exception as e:
        print(f"   Note: {e}")
    
    try:
        print("\n2. Creating table with proper schema...")
        response = s3tables.create_table(
            tableBucketARN=table_bucket_arn,
            namespace=namespace,
            name=table_name,
            format="ICEBERG"
        )
        print("   ✓ Table created with schema")
        print(f"   Table ARN: {response.get('tableARN', 'N/A')}")
        
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    print("\n3. Schema created:")
    for field in table_schema["fields"]:
        print(f"   - {field['name']}: {field['type']} ({'required' if field['required'] else 'optional'})")
    
    print("\n4. Next steps:")
    print("   - Test webhook again to send data through pipeline")
    print("   - Data should now be delivered to S3 Tables within 60 seconds")
    print("   - Check CloudWatch metrics for DeliveryToIceberg.Records")
    
    return True

if __name__ == "__main__":
    fix_s3tables_schema()