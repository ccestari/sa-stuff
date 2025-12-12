#!/bin/bash

echo "=== 1. Get ALL Firehose Log Streams ==="
aws logs describe-log-streams \
  --log-group-name /aws/kinesisfirehose/meraki-firehose \
  --order-by LastEventTime \
  --descending \
  --region us-east-1

echo -e "\n=== 2. Get DestinationDelivery Logs (Last 48h) ==="
aws logs get-log-events \
  --log-group-name /aws/kinesisfirehose/meraki-firehose \
  --log-stream-name DestinationDelivery \
  --start-time $(($(date +%s) - 172800))000 \
  --region us-east-1 \
  --limit 100 | jq -r '.events[]? | .message'

echo -e "\n=== 3. Download a Failed Iceberg Record ==="
aws s3 cp s3://edna-meraki-firehose-backup/iceberg-failed/2025/11/19/22/meraki-firehose-4-2025-11-19-22-30-48-c0357a0f-495d-4eb6-9383-66b7d9347e15 - | head -50

echo -e "\n=== 4. Check Firehose Metrics ==="
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name DeliveryToS3.Success \
  --dimensions Name=DeliveryStreamName,Value=meraki-firehose \
  --start-time $(date -u -v-24H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
