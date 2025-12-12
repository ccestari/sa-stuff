# Work Computer Setup Guide (macOS)

## Prerequisites

- macOS with VPN access
- Python 3.9+
- Git
- AWS SSO access

## Step 1: Clone Repository

```bash
cd ~/projects  # or your preferred location
git clone YOUR_REPO_URL
cd meraki-webhook-streaming
```

## Step 2: Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install boto3 psycopg2-binary paramiko==2.12.0 sshtunnel==0.4.0 pyyaml
```

## Step 3: Create Credentials File

```bash
# Copy template
cp credentials.yaml.template credentials.yaml

# Edit with your credentials
nano credentials.yaml  # or use your preferred editor
```

Get AWS credentials from:
1. Go to: https://d-9067640efb.awsapps.com/start/#
2. Select account (309820967897 for production)
3. Click "Command line or programmatic access"
4. Copy credentials from Option 2
5. Paste into credentials.yaml

**Note**: Credentials expire every 30 minutes!

## Step 4: Connect to VPN

**CRITICAL**: You must be on VPN to access the SSH bastion host (44.207.39.121)

Test SSH connection:
```bash
ssh chris.cestari@44.207.39.121
```

If this works, you're ready to proceed.

## Step 5: Setup Redshift Schema

```bash
python setup_redshift_schema.py
```

This will:
- Connect via SSH tunnel to bastion host
- Create schema: edna_stream_meraki
- Create table: meraki_webhooks
- Create views: recent_alerts, temperature_alerts

## Step 6: Deploy Infrastructure

```bash
python deploy_infrastructure.py
```

This will create:
- S3 bucket: edna-stream-meraki
- Lambda function: meraki-webhook-processor
- API Gateway: meraki-webhook-api
- Kinesis Firehose: meraki-redshift-stream
- IAM roles and policies

**Save the API Gateway URL from the output!**

## Step 7: Test Webhook

```bash
python test_webhook.py
```

This sends test webhooks to verify the pipeline works.

## Step 8: Configure Meraki Dashboard

1. Log into Meraki Dashboard
2. Go to Network-wide > Alerts
3. Add webhook with the API Gateway URL from Step 6
4. Select alert types to receive

## Optional: Load Historical Data

```bash
# Copy 3,336 historical files from nonproduction to production
python copy_historical_data.py
```

## Troubleshooting

### SSH Connection Timeout
- Verify you're on VPN
- Test: `ssh chris.cestari@44.207.39.121`

### AWS Credentials Expired
- Refresh credentials.yaml with new credentials from AWS SSO
- Credentials expire every 30 minutes

### Python Module Not Found
```bash
pip install boto3 psycopg2-binary paramiko==2.12.0 sshtunnel==0.4.0 pyyaml
```

### Permission Denied
```bash
chmod +x *.py
```

## Quick Reference

### File Locations
- **Config**: config.json
- **Credentials**: credentials.yaml (create from template)
- **Deployment Guide**: CLAUDE_DEPLOYMENT_PROMPT.md

### Key Commands
```bash
# Refresh AWS credentials
# Edit credentials.yaml with fresh credentials from AWS SSO

# Setup Redshift (requires VPN)
python setup_redshift_schema.py

# Deploy infrastructure
python deploy_infrastructure.py

# Test webhook
python test_webhook.py

# Check logs
aws logs tail /aws/lambda/meraki-webhook-processor --follow
```

### Important Notes
- **VPN Required**: For Redshift access via SSH bastion
- **Credentials Expire**: Every 30 minutes
- **Database**: db02 (not talent_acquisition)
- **S3 Bucket**: edna-stream-meraki
- **Schema**: edna_stream_meraki

## Success Criteria

✅ SSH connection to bastion host works
✅ Redshift schema created successfully
✅ Infrastructure deployed (API Gateway URL received)
✅ Test webhook returns 200 OK
✅ Data appears in Redshift within 5 minutes

## Next Steps After Deployment

1. Configure Meraki Dashboard with webhook URL
2. Monitor CloudWatch logs for incoming webhooks
3. Query Redshift to verify data:
   ```sql
   SELECT * FROM edna_stream_meraki.recent_alerts LIMIT 10;
   ```
4. Optional: Load historical data (3,336 files)
