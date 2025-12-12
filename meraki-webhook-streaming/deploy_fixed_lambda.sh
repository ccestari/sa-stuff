#!/bin/bash

# Deploy the fixed transformation Lambda

echo "=== Deploying Fixed Transformation Lambda ==="

# Create deployment package
echo "1. Creating deployment package..."
cp fix_transformation_lambda_duplicate.py lambda_function.py
zip -r transformation-lambda-fixed.zip lambda_function.py

# Update the Lambda function
echo "2. Updating Lambda function..."
aws lambda update-function-code \
  --function-name firehose-data-transformation \
  --zip-file fileb://transformation-lambda-fixed.zip

echo "3. Waiting for update to complete..."
aws lambda wait function-updated \
  --function-name firehose-data-transformation

echo "4. Testing with sample webhook..."
curl -X POST https://8eb1a48hw2.execute-api.us-east-1.amazonaws.com/prod/webhooks \
  -H 'Content-Type: application/json' \
  -d '{"alertData": {"alertType": "settings_changed", "deviceSerial": "Q2XX-XXXX-XXXX", "deviceName": "Test Device"}, "organizationName": "Test Organization", "networkName": "Test Network", "deviceSerial": "Q2XX-XXXX-XXXX"}'

echo ""
echo "5. Lambda function updated successfully!"
echo "   Wait 60+ seconds, then check CloudWatch metrics for DeliveryToIceberg.Records"

# Cleanup
rm lambda_function.py transformation-lambda-fixed.zip