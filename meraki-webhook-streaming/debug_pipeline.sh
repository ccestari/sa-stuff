#!/bin/bash

# Debug script for Meraki webhook -> Lambda -> Firehose -> Iceberg pipeline
# Account: 309820967897, Region: us-east-1

echo "=== 1. Check Lambda Function (Webhook Handler) ==="
aws lambda get-function --function-name edna-meraki-iceberg-load-from-webhook --region us-east-1

echo -e "\n=== 2. Check Lambda Logs (Last 10 minutes) ==="
aws logs tail /aws/lambda/edna-meraki-iceberg-load-from-webhook --since 10m --region us-east-1

echo -e "\n=== 3. Check Firehose Delivery Stream ==="
aws firehose describe-delivery-stream --delivery-stream-name meraki-firehose --region us-east-1

echo -e "\n=== 4. Check Firehose Metrics (Last Hour) ==="
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=meraki-firehose \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-1

echo -e "\n=== 5. Check Transformation Lambda Logs ==="
aws logs tail /aws/lambda/firehose-data-transformation --since 10m --region us-east-1

echo -e "\n=== 6. Check S3 Tables Bucket ==="
aws s3tables list-tables --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki --region us-east-1

echo -e "\n=== 7. Check Firehose Error Logs ==="
FIREHOSE_LOG_GROUP=$(aws firehose describe-delivery-stream --delivery-stream-name meraki-firehose --region us-east-1 --query 'DeliveryStreamDescription.Destinations[0].ExtendedS3DestinationDescription.CloudWatchLoggingOptions.LogGroupName' --output text)
if [ "$FIREHOSE_LOG_GROUP" != "None" ]; then
  aws logs tail $FIREHOSE_LOG_GROUP --since 10m --region us-east-1
fi

echo -e "\n=== 8. Test Lambda Invocation ==="
echo '{"test": "data"}' | aws lambda invoke \
  --function-name edna-meraki-iceberg-load-from-webhook \
  --payload file:///dev/stdin \
  --region us-east-1 \
  /tmp/lambda-response.json && cat /tmp/lambda-response.json
