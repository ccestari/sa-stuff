#!/bin/bash

echo "=== 1. Check S3 Tables Schema ==="
aws s3tables get-table --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki --namespace meraki_namespace --name raw_meraki_payload --region us-east-1

echo -e "\n=== 2. Check Glue Catalog Database ==="
aws glue get-database --name meraki_namespace --region us-east-1 2>/dev/null || echo "Database not found in Glue"

echo -e "\n=== 3. Check Glue Catalog Table ==="
aws glue get-table --database-name meraki_namespace --name raw_meraki_payload --region us-east-1 2>/dev/null || echo "Table not found in Glue"

echo -e "\n=== 4. List all databases in Glue ==="
aws glue get-databases --region us-east-1 --query 'DatabaseList[*].Name'

echo -e "\n=== 5. Check Lake Formation Permissions ==="
aws lakeformation list-permissions --region us-east-1 --max-results 20
