#!/bin/bash

echo "=== 1. Check Recent Iceberg Failures ==="
aws s3 cp s3://edna-meraki-firehose-backup/iceberg-failed/2025/11/19/22/meraki-firehose-4-2025-11-19-22-30-48-c0357a0f-495d-4eb6-9383-66b7d9347e15 - | head -20

echo -e "\n=== 2. Check Recent Processing Failures ==="
aws s3 cp s3://edna-meraki-firehose-backup/processing-failed/2025/11/19/22/meraki-firehose-4-2025-11-19-22-20-27-141c1d3d-83c9-4133-8493-1bb9fdf08598 - | head -20

echo -e "\n=== 3. Check Transformation Lambda Code ==="
aws lambda get-function --function-name firehose-data-transformation --region us-east-1 --query 'Configuration.[Handler,Runtime,Timeout,MemorySize]'

echo -e "\n=== 4. Get Transformation Lambda Logs (Last 24h) ==="
aws logs filter-log-events \
  --log-group-name /aws/lambda/firehose-data-transformation \
  --start-time $(($(date +%s) - 86400))000 \
  --region us-east-1 \
  --max-items 20

echo -e "\n=== 5. Check Firehose Detailed Logs ==="
aws logs filter-log-events \
  --log-group-name /aws/kinesisfirehose/meraki-firehose \
  --start-time $(($(date +%s) - 86400))000 \
  --filter-pattern "ERROR" \
  --region us-east-1 \
  --max-items 10
