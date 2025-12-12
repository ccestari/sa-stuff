#!/usr/bin/env python3

import boto3
import json
from datetime import datetime, timedelta

def check_s3tables_delivery():
    """Check S3 Tables delivery status and schema"""
    
    # Initialize clients
    s3tables = boto3.client('s3tables')
    firehose = boto3.client('firehose')
    cloudwatch = boto3.client('cloudwatch')
    
    table_bucket_arn = "arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki"
    namespace = "meraki_namespace"
    table_name = "raw_meraki_payload"
    stream_name = "meraki-firehose"
    
    print("=== S3 Tables Delivery Check ===\n")
    
    # 1. Check table schema
    try:
        print("1. Checking S3 Tables schema...")
        response = s3tables.get_table_metadata_location(
            tableBucketARN=table_bucket_arn,
            namespace=namespace,
            name=table_name
        )
        print(f"   Metadata location: {response.get('metadataLocation', 'Not found')}")
        print(f"   Warehouse location: {response.get('warehouseLocation', 'Not found')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Check Firehose destination config
    try:
        print("\n2. Checking Firehose S3 Tables destination...")
        response = firehose.describe_delivery_stream(DeliveryStreamName=stream_name)
        
        destinations = response['DeliveryStreamDescription']['Destinations']
        for dest in destinations:
            if 'IcebergDestinationDescription' in dest:
                iceberg_config = dest['IcebergDestinationDescription']
                print(f"   Destination table: {iceberg_config.get('DestinationTableConfigurationList', [])}")
                print(f"   Catalog config: {iceberg_config.get('CatalogConfiguration', {})}")
                
                # Check schema evolution
                schema_evolution = iceberg_config.get('SchemaEvolutionConfiguration', {})
                print(f"   Schema evolution enabled: {schema_evolution.get('Enabled', False)}")
                
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Check recent CloudWatch metrics with broader time range
    try:
        print("\n3. Checking CloudWatch metrics (last 2 hours)...")
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=2)
        
        metrics_to_check = [
            'DeliveryToIceberg.Records',
            'DeliveryToIceberg.Success', 
            'DeliveryToIceberg.DataFreshness',
            'IncomingRecords',
            'ProcessingErrors'
        ]
        
        for metric in metrics_to_check:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/Kinesis/Firehose',
                    MetricName=metric,
                    Dimensions=[{'Name': 'DeliveryStreamName', 'Value': stream_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Sum', 'Average'] if 'Records' in metric else ['Average']
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    latest = max(datapoints, key=lambda x: x['Timestamp'])
                    value = latest.get('Sum', latest.get('Average', 0))
                    print(f"   {metric}: {value} (at {latest['Timestamp']})")
                else:
                    print(f"   {metric}: No data")
                    
            except Exception as e:
                print(f"   {metric}: Error - {e}")
                
    except Exception as e:
        print(f"   Error checking metrics: {e}")
    
    # 4. Sample transformed data format
    print("\n4. Expected transformed data format for S3 Tables:")
    print("   The transformation Lambda should output JSON with these fields:")
    print("   - timestamp (string)")
    print("   - alert_type (string)")  
    print("   - organization_name (string)")
    print("   - network_name (string)")
    print("   - device_serial (string)")
    print("   - alert_data (string - JSON)")
    print("   - raw_payload (string - full original)")

if __name__ == "__main__":
    check_s3tables_delivery()