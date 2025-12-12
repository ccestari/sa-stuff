#!/bin/bash

echo "=== Testing with Real Meraki Payload ==="
cat > /tmp/real-meraki-payload.json << 'EOF'
{"timestamp":"2025-11-17T18:30:39.585490","source":"meraki-webhook","lambda_request_id":"test-123","environment":"non-prod","payload":{"version":"0.1","sharedSecret":"test","sentAt":"2025-11-17T18:30:39.278509Z","organizationId":"25998","organizationName":"Success Charter Network","networkId":"L_570831252769213811","networkName":"HSLA-MA-SENSOR","deviceSerial":"Q3CA-D536-TQKA","deviceMac":"bc:33:40:ff:c4:17","deviceName":"HSLA-MA-437","deviceModel":"MT10","alertType":"Power supply went down","alertTypeId":"power_supply_down","alertLevel":"critical","occurredAt":"2025-11-17T18:30:39.269229Z","alertData":{"num":2}}}
EOF

echo "Invoking Lambda..."
aws lambda invoke \
  --function-name edna-meraki-iceberg-load-from-webhook \
  --cli-binary-format raw-in-base64-out \
  --payload file:///tmp/real-meraki-payload.json \
  --region us-east-1 \
  /tmp/lambda-real-response.json

echo -e "\nLambda Response:"
cat /tmp/lambda-real-response.json
echo ""

echo -e "\nWaiting 10s for logs..."
sleep 10

echo -e "\n=== Lambda Logs ==="
aws logs tail /aws/lambda/edna-meraki-iceberg-load-from-webhook --since 2m --region us-east-1 --format short

echo -e "\n=== Transformation Lambda Logs ==="
aws logs tail /aws/lambda/firehose-data-transformation --since 2m --region us-east-1 --format short 2>/dev/null || echo "No transformation logs yet"

echo -e "\n=== Firehose Logs ==="
aws logs tail /aws/kinesisfirehose/meraki-firehose --since 2m --region us-east-1 --format short 2>/dev/null || echo "No firehose logs yet"
