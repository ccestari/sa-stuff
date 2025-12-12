#!/bin/bash

echo "Updating Firehose destination configuration..."

aws firehose update-destination \
  --delivery-stream-name meraki-firehose \
  --version-id 3 \
  --destination-id destinationId-000000000001 \
  --iceberg-destination-update '{
    "CatalogConfiguration": {
      "CatalogArn": "arn:aws:glue:us-east-1:309820967897:catalog"
    },
    "DestinationTableConfigurationList": [
      {
        "DestinationDatabaseName": "s3tablescatalog",
        "DestinationTableName": "lakehouse-meraki"
      }
    ]
  }' \
  --region us-east-1

echo "Firehose destination updated!"