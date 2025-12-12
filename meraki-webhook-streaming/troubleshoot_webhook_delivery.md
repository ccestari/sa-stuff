# Troubleshooting Webhook to S3 Tables Delivery

## Current Issue
Webhook triggers are not resulting in records appearing in S3 Iceberg tables despite Lambda function appearing to execute successfully.

## Quick Diagnosis Steps

### 1. Refresh AWS Credentials
```bash
# If using SSO
aws sso login

# Or check current credentials
aws sts get-caller-identity
```

### 2. Run Status Check
```bash
python3 check_firehose_status.py
```

### 3. Manual Verification Steps

#### Check Lambda Permissions
```bash
aws iam get-role-policy --role-name edna-meraki-iceberg-load-from-webhook-role-dsx7jtkc --policy-name FirehosePermissions
```

#### Check Recent Lambda Invocations
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/edna-meraki-iceberg-load-from-webhook"
aws logs filter-log-events --log-group-name "/aws/lambda/edna-meraki-iceberg-load-from-webhook" --start-time $(date -d '1 hour ago' +%s)000
```

#### Check Firehose Metrics
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Kinesis/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=meraki-firehose \
  --start-time $(date -d '1 hour ago' --iso-8601) \
  --end-time $(date --iso-8601) \
  --period 300 \
  --statistics Sum
```

## Common Issues & Fixes

### Issue 1: Lambda Missing Firehose Permissions
**Symptoms**: Lambda logs show "success" but Firehose shows 0 incoming records
**Fix**: Add Firehose permissions to Lambda role
```bash
aws iam put-role-policy --role-name edna-meraki-iceberg-load-from-webhook-role-dsx7jtkc --policy-name FirehosePermissions --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["firehose:PutRecord", "firehose:PutRecordBatch"],
      "Resource": "arn:aws:firehose:us-east-1:309820967897:deliverystream/meraki-firehose"
    }
  ]
}'
```

### Issue 2: Wrong Firehose Stream Name
**Check**: Verify Lambda is sending to correct stream
```bash
aws lambda get-function --function-name edna-meraki-iceberg-load-from-webhook
```

### Issue 3: Webhook Not Triggering Lambda
**Check**: Verify webhook URL and API Gateway configuration
```bash
aws apigateway get-rest-apis
```

### Issue 4: Data Format Issues
**Check**: Verify data format matches S3 Tables schema
- Check Lambda transformation function
- Verify Iceberg table schema

## Testing Steps

### 1. Test Lambda Directly
```bash
aws lambda invoke --function-name edna-meraki-iceberg-load-from-webhook --payload '{"test": "data"}' response.json
```

### 2. Test Firehose Directly
```bash
aws firehose put-record --delivery-stream-name meraki-firehose --record '{"Data": "{\"test\": \"data\"}"}'
```

### 3. Check S3 Tables
```bash
aws s3tables list-tables --namespace meraki_namespace --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki
```

## Key Resources
- **Firehose Stream**: `meraki-firehose`
- **Lambda Function**: `edna-meraki-iceberg-load-from-webhook`
- **S3 Tables Bucket**: `lakehouse-meraki`
- **Table**: `meraki_namespace.raw_meraki_payload`
- **Lambda Role**: `edna-meraki-iceberg-load-from-webhook-role-dsx7jtkc`