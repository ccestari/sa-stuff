#!/usr/bin/env python3
import boto3
import json

def update_firehose_destination():
    firehose = boto3.client('firehose', region_name='us-east-1')
    
    # Get current configuration
    response = firehose.describe_delivery_stream(DeliveryStreamName='meraki-firehose')
    current_config = response['DeliveryStreamDescription']
    
    # Update destination configuration
    destination_id = current_config['Destinations'][0]['DestinationId']
    
    update_params = {
        'DeliveryStreamName': 'meraki-firehose',
        'CurrentDeliveryStreamVersionId': current_config['VersionId'],
        'DestinationId': destination_id,
        'IcebergDestinationUpdate': {
            'RoleArn': 'arn:aws:iam::309820967897:role/EdnaFirehoseToS3Iceberg',
            'CatalogConfiguration': {
                'CatalogArn': 'arn:aws:glue:us-east-1:309820967897:catalog'
            },
            'DestinationTableConfigurationList': [
                {
                    'DestinationTableName': 'lakehouse-meraki',
                    'DestinationDatabaseName': 's3tablescatalog',
                    'S3ErrorOutputPrefix': 'errors/'
                }
            ],
            'BufferingHints': {
                'SizeInMBs': 5,
                'IntervalInSeconds': 60
            },
            'S3Configuration': {
                'RoleArn': 'arn:aws:iam::309820967897:role/EdnaFirehoseToS3Iceberg',
                'BucketArn': 'arn:aws:s3:::edna-firehose-backup',
                'Prefix': 'greenhouse-backup/',
                'ErrorOutputPrefix': 'errors/',
                'BufferingHints': {
                    'SizeInMBs': 5,
                    'IntervalInSeconds': 300
                },
                'CompressionFormat': 'GZIP'
            }
        }
    }
    
    try:
        response = firehose.update_destination(**update_params)
        print("✅ Firehose destination updated successfully")
        print(f"Version ID: {response.get('VersionId', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Error updating Firehose destination: {e}")
        return False

if __name__ == "__main__":
    print("=== Updating Firehose Destination Configuration ===")
    update_firehose_destination()