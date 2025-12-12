#!/bin/bash

echo "=== AWS Firehose S3 Tables Delivery Check ==="
echo

echo "1. Testing AWS Access..."
aws sts get-caller-identity
if [ $? -ne 0 ]; then
    echo "ERROR: AWS credentials not working. Please refresh your credentials."
    exit 1
fi

echo
echo "2. Checking Firehose Configuration..."
aws firehose describe-delivery-stream --delivery-stream-name meraki-firehose --region us-east-1

echo
echo "3. Checking Lambda Function..."
aws lambda get-function --function-name firehose-data-transformation --region us-east-1

echo
echo "4. Checking Glue Database..."
aws glue get-database --catalog-id 309820967897 --name s3tablescatalog --region us-east-1

echo
echo "5. Checking Glue Table..."
aws glue get-table --catalog-id 309820967897 --database-name s3tablescatalog --name lakehouse-meraki --region us-east-1

echo
echo "=== Check Complete ==="