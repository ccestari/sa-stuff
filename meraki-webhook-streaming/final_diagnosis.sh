#!/bin/bash

# Check credentials
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "❌ Run: aws sso login --profile AWSAdministratorAccess-309820967897"
  exit 1
fi

echo "✅ Credentials valid"
echo ""

# The transformation Lambda is WORKING - it returns 'result': 'Ok'
# The issue is likely in the Iceberg table schema or Firehose->Iceberg connection

echo "=== 1. Firehose Destination Logs (Last 48h) ==="
aws logs filter-log-events \
  --log-group-name /aws/kinesisfirehose/meraki-firehose \
  --log-stream-name-prefix DestinationDelivery \
  --start-time $(($(date +%s) - 172800))000 \
  --region us-east-1 \
  --max-items 30 2>&1 | jq -r '.events[]? | .message' | tail -30

echo -e "\n=== 2. S3 Tables Schema ==="
aws s3tables get-table \
  --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki \
  --namespace meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1 2>&1

echo -e "\n=== 3. Glue Catalog Table Schema ==="
aws glue get-table \
  --database-name meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1 2>&1 | jq '.Table.StorageDescriptor.Columns'

echo -e "\n=== 4. Expected Data Structure (from Lambda) ==="
cat << 'EOF'
{
  "alert_timestamp": "string",
  "alert_source": "string", 
  "lambda_request_id": "string",
  "environment": "string",
  "webhook_version": "string",
  "shared_secret": "string",
  "alert_sent_at": "string",
  "organization_id": "string",
  "organization_name": "string",
  "organization_url": "string",
  "network_id": "string",
  "network_name": "string",
  "network_url": "string",
  "network_tags": "string/null",
  "device_serial": "string",
  "device_mac": "string",
  "device_name": "string",
  "device_url": "string",
  "device_tags": "string",
  "device_model": "string",
  "alert_id": "string",
  "alert_type": "string",
  "alert_type_id": "string",
  "alert_level": "string",
  "alert_occurred_at": "string",
  "num": "integer"
}
EOF

echo -e "\n=== 5. Check Recent Iceberg Failed Records ==="
aws s3 ls s3://edna-meraki-firehose-backup/iceberg-failed/ --recursive | tail -5

echo -e "\n=== SUMMARY ==="
echo "✅ Webhook Lambda: Working"
echo "✅ Firehose: Receiving data"
echo "✅ Transformation Lambda: Working (returns 'Ok')"
echo "❌ Iceberg Write: FAILING"
echo ""
echo "Next: Compare table schema with data structure above"
