#!/usr/bin/env python3

import boto3
import json

def enable_schema_evolution():
    """Enable schema evolution in Firehose to allow automatic schema creation"""
    
    firehose = boto3.client('firehose')
    
    stream_name = "meraki-firehose"
    
    print("=== Enabling Schema Evolution ===\n")
    
    try:
        print("1. Getting current Firehose configuration...")
        response = firehose.describe_delivery_stream(DeliveryStreamName=stream_name)
        
        current_config = response['DeliveryStreamDescription']['Destinations'][0]['IcebergDestinationDescription']
        
        print("2. Updating Firehose with schema evolution enabled...")
        
        # Update the delivery stream to enable schema evolution
        update_response = firehose.update_destination(
            DeliveryStreamName=stream_name,
            CurrentDeliveryStreamVersionId=response['DeliveryStreamDescription']['VersionId'],
            DestinationId="destinationId-000000000001",
            IcebergDestinationUpdate={
                'SchemaEvolutionConfiguration': {
                    'Enabled': True
                }
            }
        )
        
        print("   ✓ Schema evolution enabled")
        print(f"   New version: {update_response.get('VersionId', 'N/A')}")
        
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    print("\n3. Schema evolution is now enabled")
    print("   - S3 Tables will automatically create schema from first data batch")
    print("   - Future schema changes will be handled automatically")
    
    print("\n4. Test the pipeline:")
    print("   curl -X POST https://8eb1a48hw2.execute-api.us-east-1.amazonaws.com/prod/webhooks \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"alertData\": {\"alertType\": \"test\"}, \"organizationName\": \"Test Org\", \"networkName\": \"Test Network\", \"deviceSerial\": \"TEST123\"}'")
    
    return True

if __name__ == "__main__":
    enable_schema_evolution()