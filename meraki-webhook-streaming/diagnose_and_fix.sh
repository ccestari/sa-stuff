#!/bin/bash

# Re-authenticate first
echo "Checking AWS credentials..."
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "❌ AWS credentials expired. Please run:"
  echo "   aws sso login --profile AWSAdministratorAccess-309820967897"
  exit 1
fi

echo "✅ AWS credentials valid"
echo ""

# 1. Check transformation Lambda logs
echo "=== 1. Transformation Lambda Logs (Last 24h) ==="
aws logs tail /aws/lambda/firehose-data-transformation --since 24h --region us-east-1 --format short 2>&1 | head -100

# 2. Check Firehose logs for errors
echo -e "\n=== 2. Firehose Error Logs ==="
aws logs filter-log-events \
  --log-group-name /aws/kinesisfirehose/meraki-firehose \
  --start-time $(($(date +%s) - 86400))000 \
  --region us-east-1 \
  --max-items 20 2>&1 | jq -r '.events[]? | .message' | head -50

# 3. Check table schema
echo -e "\n=== 3. S3 Tables Schema ==="
aws s3tables get-table \
  --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki \
  --namespace meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1 2>&1

# 4. Download and examine a failed record
echo -e "\n=== 4. Sample Failed Record ==="
aws s3 ls s3://edna-meraki-firehose-backup/processing-failed/ --recursive | tail -1 | awk '{print $4}' | xargs -I {} aws s3 cp s3://edna-meraki-firehose-backup/{} - 2>/dev/null | head -20

# 5. Check transformation Lambda function code
echo -e "\n=== 5. Transformation Lambda Configuration ==="
aws lambda get-function --function-name firehose-data-transformation --region us-east-1 --query 'Configuration.[Handler,Runtime,Timeout,MemorySize,LastModified]'

echo -e "\n=== DIAGNOSIS COMPLETE ==="
echo "Review the output above to identify:"
echo "1. Transformation Lambda errors"
echo "2. Schema mismatches"
echo "3. Permission issues"
