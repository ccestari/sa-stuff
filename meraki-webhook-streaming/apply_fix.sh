#!/bin/bash

echo "=== Fixing Glue Catalog to S3 Tables Sync ==="

# Get warehouse location
WAREHOUSE_LOC=$(aws s3tables get-table \
  --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki \
  --namespace meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1 \
  --query 'warehouseLocation' \
  --output text)

echo "S3 Tables Warehouse Location: $WAREHOUSE_LOC"

# Get current Glue table location
GLUE_LOC=$(aws glue get-table \
  --database-name meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1 \
  --query 'Table.StorageDescriptor.Location' \
  --output text)

echo "Current Glue Table Location: $GLUE_LOC"

if [ "$WAREHOUSE_LOC" = "$GLUE_LOC" ]; then
  echo "✅ Locations match! Issue is elsewhere."
else
  echo "❌ Locations don't match. Updating Glue table..."
  
  # Get current columns
  COLUMNS=$(aws glue get-table \
    --database-name meraki_namespace \
    --name raw_meraki_payload \
    --region us-east-1 \
    --query 'Table.StorageDescriptor.Columns' \
    --output json)
  
  # Update table
  aws glue update-table \
    --database-name meraki_namespace \
    --region us-east-1 \
    --table-input "{
      \"Name\": \"raw_meraki_payload\",
      \"StorageDescriptor\": {
        \"Location\": \"$WAREHOUSE_LOC\",
        \"InputFormat\": \"org.apache.iceberg.mr.mapred.MapredIcebergInputFormat\",
        \"OutputFormat\": \"org.apache.iceberg.mr.mapred.MapredIcebergOutputFormat\",
        \"SerdeInfo\": {
          \"SerializationLibrary\": \"org.apache.iceberg.mr.hive.HiveIcebergSerDe\"
        },
        \"Columns\": $COLUMNS
      },
      \"TableType\": \"EXTERNAL_TABLE\",
      \"Parameters\": {
        \"table_type\": \"ICEBERG\",
        \"metadata_location\": \"$WAREHOUSE_LOC/metadata\"
      }
    }"
  
  echo "✅ Glue table updated!"
fi

echo -e "\n=== Test with new webhook ==="
echo "Send a test webhook or wait for next real webhook to verify fix."
