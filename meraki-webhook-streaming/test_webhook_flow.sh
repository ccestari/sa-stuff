#!/bin/bash

# Test the complete webhook flow with sample data

echo "=== Testing Lambda with Sample Meraki Webhook Payload ==="
cat > /tmp/meraki-test-payload.json << 'EOF'
{"version":"0.1","sharedSecret":"test","sentAt":"2024-01-01T00:00:00.000000Z","organizationId":"123456","networkId":"N_123456","deviceSerial":"Q2XX-XXXX-XXXX","deviceMac":"00:11:22:33:44:55"}
EOF

aws lambda invoke \
  --function-name edna-meraki-iceberg-load-from-webhook \
  --cli-binary-format raw-in-base64-out \
  --payload file:///tmp/meraki-test-payload.json \
  --region us-east-1 \
  /tmp/lambda-test-response.json

echo -e "\n=== Lambda Response ==="
cat /tmp/lambda-test-response.json

echo -e "\n\n=== Check if Firehose received data (wait 30s) ==="
sleep 30

aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=meraki-firehose \
  --start-time $(date -u -v-5M +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum \
  --region us-east-1
