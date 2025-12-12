#!/bin/bash

echo "=== Problem: Firehose can't find table in Glue Catalog ==="
echo "Error: Iceberg.NoSuchTable"
echo ""

echo "=== 1. Check if Glue Database Exists ==="
aws glue get-database --name meraki_namespace --region us-east-1 2>&1

echo -e "\n=== 2. Check if Glue Table Exists ==="
aws glue get-table --database-name meraki_namespace --name raw_meraki_payload --region us-east-1 2>&1 | jq '.Table | {Name, DatabaseName, StorageDescriptor: {Location}}'

echo -e "\n=== 3. Get S3 Tables Metadata Location ==="
aws s3tables get-table \
  --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki \
  --namespace meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1 | jq '{metadataLocation, warehouseLocation}'

echo -e "\n=== SOLUTION ==="
echo "The Glue table location must match the S3 Tables warehouse location."
echo ""
echo "Run this to update the Glue table location:"
echo ""
cat << 'EOF'
# Get the warehouse location from S3 Tables
WAREHOUSE_LOC=$(aws s3tables get-table \
  --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki \
  --namespace meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1 \
  --query 'warehouseLocation' \
  --output text)

echo "Warehouse location: $WAREHOUSE_LOC"

# Update Glue table to point to S3 Tables location
aws glue update-table \
  --database-name meraki_namespace \
  --region us-east-1 \
  --table-input "{
    \"Name\": \"raw_meraki_payload\",
    \"StorageDescriptor\": {
      \"Location\": \"$WAREHOUSE_LOC\",
      \"InputFormat\": \"org.apache.hadoop.mapred.FileInputFormat\",
      \"OutputFormat\": \"org.apache.hadoop.mapred.FileOutputFormat\",
      \"SerdeInfo\": {
        \"SerializationLibrary\": \"org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe\"
      },
      \"Columns\": $(aws glue get-table --database-name meraki_namespace --name raw_meraki_payload --region us-east-1 --query 'Table.StorageDescriptor.Columns' --output json)
    },
    \"TableType\": \"EXTERNAL_TABLE\"
  }"
EOF
