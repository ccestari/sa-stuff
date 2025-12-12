# Webhook Utilities

Generic utilities for managing webhook streaming projects (Meraki, Greenhouse, etc.)

## Prerequisites

```bash
pip install boto3 pyyaml requests
```

## Configuration

All scripts expect:
- `config.json` - Project configuration with AWS resources
- `credentials.yaml` - AWS credentials (production/nonproduction)

## Scripts

### check_s3_data.py
Check S3 bucket for webhook data

```bash
python3 check_s3_data.py [config.json] [credentials.yaml]
```

### check_lambda_logs.py
Check Lambda CloudWatch logs

```bash
python3 check_lambda_logs.py [config.json] [credentials.yaml] [hours]
```

### test_webhook.py
Test webhook endpoint

```bash
python3 test_webhook.py --url https://xxx.execute-api.us-east-1.amazonaws.com/prod/webhook [--count 5] [--payload payload.json]
```

### update_lambda.py
Update Lambda function code

```bash
python3 update_lambda.py [config.json] [credentials.yaml] [lambda_function.py]
```

### invoke_lambda_directly.py
Invoke Lambda directly to test

```bash
python3 invoke_lambda_directly.py [config.json] [credentials.yaml]
```

### fix_api_gateway.py
Fix API Gateway Lambda permissions

```bash
python3 fix_api_gateway.py [config.json] [credentials.yaml]
```

## Usage Example

```bash
cd /path/to/webhook-project

# Check if webhooks are flowing
python3 ../sa-utils/webhook-utils/check_s3_data.py

# Check Lambda logs
python3 ../sa-utils/webhook-utils/check_lambda_logs.py

# Test endpoint
python3 ../sa-utils/webhook-utils/test_webhook.py --url https://xxx.execute-api.us-east-1.amazonaws.com/prod/webhook

# Update Lambda code
python3 ../sa-utils/webhook-utils/update_lambda.py

# Fix API Gateway permissions
python3 ../sa-utils/webhook-utils/fix_api_gateway.py
```

## Notes

- AWS credentials expire every 30 minutes - update `credentials.yaml` as needed
- All scripts use relative paths and work from any webhook project directory
- Scripts are anonymized and work with any webhook streaming project
