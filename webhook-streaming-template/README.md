# Webhook Streaming Template

Template for streaming webhook data to AWS Redshift via Lambda, S3, and Firehose.

## Architecture

```
Webhook Source
    ↓
API Gateway
    ↓
Lambda (process & store)
    ├→ S3 (raw JSON)
    └→ Firehose
         ↓
    Redshift
```

## Quick Start

1. **Copy template**
   ```bash
   cp -r webhook-streaming-template my-webhook-project
   cd my-webhook-project
   ```

2. **Configure**
   ```bash
   # Edit config.json - replace all YOUR_* placeholders
   nano config.json
   ```

3. **Deploy**
   ```bash
   python deploy.py  # Automatically packages sa_utils with Lambda
   ```

4. **Test**
   ```bash
   python test_webhook.py --url $(cat deployment_info.json | jq -r .api_url)
   python check_logs.py
   ```

5. **Analyze payloads**
   ```bash
   python analyze_payloads.py --bucket YOUR-webhooks-raw
   ```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## Environment Variables

Lambda requires:
- `WEBHOOK_SOURCE` - Source identifier (e.g., 'meraki_webhook')
- `ENVIRONMENT` - Environment name (default: 'production')
- `RAW_BUCKET` - S3 bucket for raw payloads (optional)
- `FIREHOSE_STREAM` - Firehose stream name (optional)

## Files

- `lambda_function.py` - Lambda handler using sa_utils
- `deploy.py` - Deploy infrastructure (bundles sa_utils automatically)
- `test_webhook.py` - Test webhook endpoint
- `check_logs.py` - Check CloudWatch logs
- `analyze_payloads.py` - Analyze webhook schemas from S3
- `config.json` - AWS configuration
- `requirements.txt` - Python dependencies
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide

## Customization

Extend `lambda_function.py` to add:
- Custom payload transformation
- Schema validation
- Additional storage destinations
- Alert notifications
