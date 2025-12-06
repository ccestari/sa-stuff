# Meraki Webhook Streaming to Redshift

Stream Meraki webhook data to AWS Redshift for analytics and monitoring.

## Architecture

```
Meraki Dashboard
    ↓ (webhook)
API Gateway
    ↓
Lambda (flatten & store)
    ↓
S3 (raw JSON)
    ↓ (scheduled COPY)
Redshift
```

## Quick Start

### Prerequisites
- Python 3.9+
- AWS credentials with access to account 309820967897
- VPN access to Redshift cluster (for sync script)

### Setup

1. **Clone and install**
   ```bash
   git clone <repo-url>
   cd meraki-webhook-streaming
   pip install -r requirements.txt
   ```

2. **Configure credentials**
   ```bash
   cp credentials.yaml.template credentials.yaml
   # Edit credentials.yaml with your AWS credentials
   ```

3. **Test connection**
   ```bash
   python check_s3_data.py
   ```

4. **Start sync** (requires VPN)
   ```bash
   python sync_s3_to_redshift.py
   # Or on macOS/Linux:
   chmod +x sync_s3_to_redshift.sh
   ./sync_s3_to_redshift.sh
   ```

## Key Files

- `lambda_function.py` - Webhook processor
- `sync_s3_to_redshift.py` - Automated S3→Redshift sync
- `setup_redshift_schema.py` - Create Redshift table
- `test_webhook.py` - Send test webhooks
- `check_s3_data.py` - Monitor S3 files
- `check_lambda_logs.py` - View Lambda logs

## Configuration

### AWS Resources
- **API Gateway**: https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook
- **Lambda**: meraki-webhook-processor
- **S3 Bucket**: edna-stream-meraki
- **Redshift**: edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com
- **Database**: db02
- **Schema**: edna_stream_meraki

### Redshift Table
- **Table**: `edna_stream_meraki.meraki_webhooks`
- **Columns**: 37 (flexible schema for all alert types)
- **Views**: `recent_alerts`, `temperature_alerts`

## How It Works

1. **Meraki sends webhook** to API Gateway
2. **Lambda receives** and flattens payload
3. **Lambda stores** raw JSON to S3
4. **Sync script** runs COPY command every 5 minutes
5. **Data appears** in Redshift for querying

## Why Not Firehose?

Firehose can't connect to Redshift because the cluster is behind a VPN/bastion. The sync script uses SSH tunnel to access Redshift.

## Monitoring

```bash
# Check S3 files
python check_s3_data.py

# Check Lambda logs
python check_lambda_logs.py

# Test webhook
python test_webhook.py --count 5
```

## Querying Data

```sql
-- Recent webhooks
SELECT * FROM edna_stream_meraki.recent_alerts LIMIT 10;

-- Temperature alerts
SELECT * FROM edna_stream_meraki.temperature_alerts 
WHERE temperature_fahrenheit > 70;

-- Count by device
SELECT device_name, COUNT(*) 
FROM edna_stream_meraki.meraki_webhooks 
GROUP BY device_name;
```

## Troubleshooting

### Credentials Expired
AWS credentials expire every 30 minutes. Update `credentials.yaml` with new credentials.

### No Data in Redshift
1. Check S3 has files: `python check_s3_data.py`
2. Check Lambda is running: `python check_lambda_logs.py`
3. Run sync manually: `python sync_s3_to_redshift.py`

### VPN Required
The sync script requires VPN access to reach Redshift via bastion host.

## Documentation

- `FINAL_STATUS.md` - Complete system status
- `CONVERSATION_LOG.md` - Development history
- `CLAUDE_DEPLOYMENT_PROMPT.md` - Deployment guide
- `DEPLOYMENT_GUIDE.md` - Detailed setup instructions

## Security

- Never commit `credentials.yaml`
- AWS credentials expire every 30 minutes
- Redshift accessible only via VPN/bastion
- Raw webhooks stored in S3 for audit

## Support

For issues or questions, see `FINAL_STATUS.md` for troubleshooting steps.
