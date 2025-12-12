#!/bin/bash

echo "=== 1. Firehose Destination Delivery Logs (Iceberg errors) ==="
aws logs filter-log-events \
  --log-group-name /aws/kinesisfirehose/meraki-firehose \
  --log-stream-name DestinationDelivery \
  --start-time $(($(date +%s) - 172800))000 \
  --region us-east-1 \
  --max-items 50 | jq -r '.events[]? | .message'

echo -e "\n=== 2. Check S3 Tables Schema ==="
aws s3tables get-table \
  --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki \
  --namespace meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1

echo -e "\n=== 3. Check Glue Catalog Table ==="
aws glue get-table \
  --database-name meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1 2>&1

echo -e "\n=== 4. Sample Transformed Data ==="
echo "The transformation Lambda outputs this structure:"
echo '{"alert_timestamp":"...","alert_source":"meraki-webhook","lambda_request_id":"...","environment":"non-prod","webhook_version":"0.1","shared_secret":"...","alert_sent_at":"...","organization_id":"25998","organization_name":"Success Charter Network","organization_url":"...","network_id":"...","network_name":"...","network_url":"...","network_tags":null,"device_serial":"...","device_mac":"...","device_name":"...","device_url":"...","device_tags":"recently-added","device_model":"...","alert_id":"","alert_type":"Power supply went down","alert_type_id":"power_supply_down","alert_level":"critical","alert_occurred_at":"...","num":2}'

echo -e "\n=== 5. Check Firehose Configuration ==="
aws firehose describe-delivery-stream \
  --delivery-stream-name meraki-firehose \
  --region us-east-1 \
  --query 'DeliveryStreamDescription.Destinations[0].IcebergDestinationDescription.{TableName:DestinationTableConfigurationList[0].DestinationTableName,Database:DestinationTableConfigurationList[0].DestinationDatabaseName,CatalogARN:CatalogConfiguration.CatalogARN}'
