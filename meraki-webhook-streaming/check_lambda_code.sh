#!/bin/bash

echo "=== Lambda Function Code (Webhook Handler) ==="
aws lambda get-function --function-name edna-meraki-iceberg-load-from-webhook --region us-east-1 --query 'Code.Location' --output text | xargs curl -s | python3 -m zipfile -l /dev/stdin

echo -e "\n=== Transformation Lambda Code ==="
aws lambda get-function --function-name firehose-data-transformation --region us-east-1 --query 'Code.Location' --output text | xargs curl -s | python3 -m zipfile -l /dev/stdin

echo -e "\n=== Check API Gateway Trigger ==="
aws lambda list-event-source-mappings --function-name edna-meraki-iceberg-load-from-webhook --region us-east-1

echo -e "\n=== Check Lambda Permissions ==="
aws lambda get-policy --function-name edna-meraki-iceberg-load-from-webhook --region us-east-1 2>/dev/null || echo "No resource-based policy found"

echo -e "\n=== Recent CloudWatch Logs (All Log Groups) ==="
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/edna-meraki --region us-east-1

echo -e "\n=== Check for ANY Lambda invocations (last 24h) ==="
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=edna-meraki-iceberg-load-from-webhook \
  --start-time $(date -u -v-24H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
