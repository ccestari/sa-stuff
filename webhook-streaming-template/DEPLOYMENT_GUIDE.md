# Webhook Streaming Deployment Guide

Complete step-by-step guide to deploy a webhook streaming pipeline to AWS Redshift.

## Prerequisites

- Python 3.11+
- AWS CLI configured with credentials
- Access to AWS account
- sa-utils installed or available locally

## Step 1: Clone Template

```bash
cp -r webhook-streaming-template my-webhook-project
cd my-webhook-project
```

## Step 2: Configure

Edit `config.json` and replace all `YOUR_*` placeholders:

```json
{
  "aws": {
    "account_id": "123456789012",  // Your AWS account ID
    "region": "us-east-1"
  },
  "lambda": {
    "function_name": "myapp-webhook-processor",  // Unique name
    ...
  },
  "s3": {
    "raw_bucket": "myapp-webhooks-raw",  // Unique bucket name
    "backup_bucket": "myapp-webhooks-backup"
  },
  ...
}
```

## Step 3: Create IAM Role

Create Lambda execution role with permissions:

```bash
aws iam create-role \
  --role-name myapp-webhook-processor-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policies
aws iam attach-role-policy \
  --role-name myapp-webhook-processor-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Add S3 and Firehose permissions (create custom policy)
```

## Step 4: Deploy Infrastructure

```bash
python deploy.py
```

This will:
- ✅ Package Lambda with sa_utils included
- ✅ Create S3 buckets for raw data and backups
- ✅ Deploy Lambda function
- ✅ Create API Gateway endpoint
- ✅ Save deployment info to `deployment_info.json`

## Step 5: Test Webhook

```bash
# Test with empty payload
python test_webhook.py --url https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/webhook

# Test with custom payload
echo '{"test": "data"}' > test_payload.json
python test_webhook.py --url YOUR_URL --payload test_payload.json --count 5
```

## Step 6: Setup Redshift (Optional)

If streaming to Redshift via Firehose:

### 6.1 Create Redshift Table

```sql
CREATE TABLE your_schema.webhooks (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ingestion_timestamp TIMESTAMP DEFAULT GETDATE(),
    timestamp VARCHAR(50),
    source VARCHAR(50),
    lambda_request_id VARCHAR(100),
    environment VARCHAR(50),
    payload_json VARCHAR(MAX)
);
```

### 6.2 Create Firehose Stream

```bash
aws firehose create-delivery-stream \
  --delivery-stream-name myapp-redshift-stream \
  --delivery-stream-type DirectPut \
  --redshift-destination-configuration file://firehose-config.json
```

## Step 7: Monitor

### Check Lambda Logs
```bash
python check_logs.py --function myapp-webhook-processor --hours 24
```

### Check S3 Data
```bash
aws s3 ls s3://myapp-webhooks-raw/raw/
```

### Query Redshift
```sql
SELECT * FROM your_schema.webhooks 
ORDER BY ingestion_timestamp DESC 
LIMIT 10;
```

## Step 8: Configure Webhook Source

Point your webhook source (e.g., Meraki, Greenhouse, etc.) to the API Gateway URL from `deployment_info.json`.

## Customization

### Add Custom Processing

Edit `lambda_function.py` to add custom logic:

```python
def process_webhook(event, context):
    body = parse_webhook_body(event)
    
    # Add your custom processing here
    if body.get('type') == 'special':
        handle_special_case(body)
    
    # Continue with standard processing
    webhook_data = add_webhook_metadata(body, context, 'my_source')
    ...
```

### Add Schema Validation

```python
def validate_payload(payload):
    required_fields = ['id', 'timestamp', 'type']
    if not all(field in payload for field in required_fields):
        raise ValueError(f"Missing required fields")
```

### Add Alerting

```python
def send_alert(message):
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:123456789012:alerts',
        Subject='Webhook Alert',
        Message=message
    )
```

## Troubleshooting

### Lambda Package Too Large

If Lambda package exceeds 50MB:
1. Remove unnecessary files from sa_utils
2. Use Lambda layers for dependencies
3. Upload to S3 instead of direct upload

### API Gateway 403 Error

Check Lambda permissions:
```bash
aws lambda get-policy --function-name myapp-webhook-processor
```

### No Data in S3

Check Lambda logs:
```bash
python check_logs.py --function myapp-webhook-processor
```

Verify environment variables:
```bash
aws lambda get-function-configuration --function-name myapp-webhook-processor
```

## Architecture Diagram

```
Webhook Source (Meraki/Greenhouse/etc)
    ↓
API Gateway (POST /webhook)
    ↓
Lambda Function
    ├→ S3 Raw Bucket (audit trail)
    └→ Kinesis Firehose
         ↓
    Redshift Table
```

## Cost Estimate

For 10,000 webhooks/day:
- API Gateway: ~$3.50/month
- Lambda: ~$0.20/month
- S3: ~$0.50/month
- Firehose: ~$8.70/month
- **Total: ~$13/month**

## Next Steps

1. Set up CloudWatch alarms for errors
2. Create Redshift views for analytics
3. Add data quality checks
4. Implement retry logic
5. Set up monitoring dashboard
