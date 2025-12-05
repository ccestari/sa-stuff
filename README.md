# Meraki Webhook Streaming to Redshift

Stream Meraki webhook data to AWS Redshift via API Gateway, Lambda, and Kinesis Firehose.

## Architecture

```
Meraki Dashboard
    ↓ (webhook)
API Gateway
    ↓
Lambda (flatten + route)
    ↓
    ├→ S3 (raw storage)
    └→ Firehose → Redshift
```

## Features

- **Flexible Schema**: Single table handles 24+ alert types with nullable columns
- **Schema Detection**: Automatic detection and alerting for unknown schemas
- **Raw Storage**: All payloads archived to S3 for audit and reprocessing
- **Error Handling**: CloudWatch/SNS alerts for unknown schemas and processing errors
- **Historical Data**: Analyzed 3,336 historical files, ready to import
- **Cross-Account**: Supports copying data from nonproduction to production

## Alert Types Supported

Based on analysis of 3,336 historical files:
- Sensor change detected (74% of alerts)
- Power supply events
- Motion detection
- Geofencing events
- AP status changes
- Client connections
- Gateway status
- And 17+ more types

## Prerequisites

- Python 3.9+
- AWS CLI configured
- VPN access (for Redshift via SSH bastion)
- AWS SSO credentials

## Quick Start

### 1. Install Dependencies

```bash
pip install boto3 psycopg2-binary paramiko==2.12.0 sshtunnel==0.4.0 pyyaml
```

### 2. Configure Credentials

Create `credentials.yaml` (gitignored):

```yaml
production:
  aws_access_key_id: YOUR_KEY
  aws_secret_access_key: YOUR_SECRET
  aws_session_token: YOUR_TOKEN
  account_id: "309820967897"

nonproduction:
  aws_access_key_id: YOUR_KEY
  aws_secret_access_key: YOUR_SECRET
  aws_session_token: YOUR_TOKEN
  account_id: "205372355929"

redshift:
  password: YOUR_REDSHIFT_PASSWORD

ssh:
  password: YOUR_SSH_PASSWORD
```

### 3. Deploy (Must be on VPN)

```bash
# Setup Redshift schema (requires VPN)
python setup_redshift_schema.py

# Deploy AWS infrastructure
python deploy_infrastructure.py

# Test webhook
python test_webhook.py
```

### 4. Configure Meraki Dashboard

Use the API Gateway URL from deployment output as your webhook endpoint.

## Configuration

See `config.json` for AWS resources:
- **Database**: db02
- **Schema**: edna_stream_meraki
- **S3 Bucket**: edna-stream-meraki
- **Redshift**: edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com

## Scripts

- `setup_redshift_schema.py` - Create Redshift schema (requires VPN)
- `deploy_infrastructure.py` - Deploy AWS resources
- `test_webhook.py` - Test webhook endpoint
- `analyze_historical_data.py` - Analyze historical webhook data
- `copy_historical_data.py` - Copy 3,336 historical files to production

## Important Notes

- **VPN Required**: Must be on VPN to access Redshift via SSH bastion (44.207.39.121)
- **Credentials Expire**: AWS credentials expire every 30 minutes
- **Platform**: All scripts work on Windows and macOS

## Troubleshooting

### SSH Connection Timeout
Ensure you're connected to VPN before running `setup_redshift_schema.py`.

### Credentials Expired
Update `credentials.yaml` with fresh credentials from AWS SSO.

### Unknown Schema Alert
Check CloudWatch logs for details. Lambda will alert via SNS if configured.

## Documentation

- `CLAUDE_DEPLOYMENT_PROMPT.md` - Detailed deployment guide for Claude AI
- `config.json` - AWS resource configuration
- `.gitignore` - Excludes credentials and sensitive files

## License

Internal use only - Success Charter Network
