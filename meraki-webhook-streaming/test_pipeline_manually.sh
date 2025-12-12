#!/bin/bash

echo "=== Test 1: Direct Lambda Invocation with Proper JSON ==="
aws lambda invoke \
  --function-name edna-meraki-iceberg-load-from-webhook \
  --cli-binary-format raw-in-base64-out \
  --payload '{"test":"data","timestamp":"2024-01-01T00:00:00Z"}' \
  --region us-east-1 \
  /tmp/lambda-response.json

echo -e "\nLambda Response:"
cat /tmp/lambda-response.json
echo ""

echo -e "\n=== Test 2: Check Lambda Logs After Invocation ==="
sleep 5
aws logs tail /aws/lambda/edna-meraki-iceberg-load-from-webhook --since 2m --region us-east-1 --format short

echo -e "\n=== Test 3: Check Firehose Metrics After Test ==="
sleep 10
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=meraki-firehose \
  --start-time $(date -u -v-5M +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum \
  --region us-east-1

echo -e "\n=== Test 4: Check Firehose Logs ==="
aws logs tail /aws/kinesisfirehose/meraki-firehose --since 2m --region us-east-1 --format short 2>/dev/null || echo "No recent Firehose logs"

echo -e "\n=== Test 5: Check Transformation Lambda Logs ==="
aws logs tail /aws/lambda/firehose-data-transformation --since 2m --region us-east-1 --format short 2>/dev/null || echo "No recent transformation logs"
