# Getting Started - Meraki Webhook Streaming

## What You Have

A complete, production-ready solution to stream Meraki webhook data to your Redshift cluster in real-time with flexible schema handling.

## What It Does

1. **Receives** Meraki webhooks via API Gateway
2. **Stores** raw JSON payloads to S3 for archival
3. **Flattens** varying webhook structures to consistent schema
4. **Streams** to Redshift via Kinesis Firehose
5. **Handles** AWS credential rotation automatically

## 5-Minute Quick Start

### Step 1: Open Terminal

```bash
cd c:\Users\cesta\OneDrive\Documents\GitHub\sa-stuff\meraki-webhook-streaming
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Initialize Credentials

Edit `init_credentials.bat` with your AWS credentials from:
https://d-9067640efb.awsapps.com/start/#

Then run:
```bash
init_credentials.bat
```

### Step 4: Run Quick Start

```bash
quick_start.bat
```

This will:
- ✅ Check AWS credentials
- ✅ Deploy all AWS infrastructure
- ✅ Create Redshift schema (you'll need passwords)
- ✅ Test the webhook endpoint

**Note**: You'll be prompted for Redshift and SSH passwords during schema setup.

### Step 5: Configure Meraki

After deployment completes, you'll see an API Gateway URL like:

```
https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/webhook
```

1. Go to Meraki Dashboard → Network-wide → Alerts
2. Add webhook receiver with this URL
3. Select alert types to send

## That's It!

Webhooks will now flow from Meraki → API Gateway → Lambda → S3 + Firehose → Redshift.

Data appears in: `edna_stream_meraki.meraki_webhooks`

## Verify It's Working

### Check Status

```bash
python check_status.py
```

### Query Redshift

```sql
-- Recent webhooks
SELECT * FROM edna_stream_meraki.meraki_webhooks 
ORDER BY ingestion_timestamp DESC 
LIMIT 10;

-- Recent alerts
SELECT * FROM edna_stream_meraki.recent_alerts 
LIMIT 20;

-- Temperature alerts
SELECT * FROM edna_stream_meraki.temperature_alerts 
WHERE occurred_at >= CURRENT_DATE - 1;
```

### View CloudWatch Logs

- Lambda: `/aws/lambda/meraki-webhook-processor`
- Firehose: `/aws/kinesisfirehose/meraki-redshift-stream`

### Check S3 Storage

```bash
# Raw payloads
aws s3 ls s3://meraki-webhooks-raw-309820967897/raw/

# Firehose backup
aws s3 ls s3://meraki-webhooks-backup-309820967897/firehose-backup/
```

## When Credentials Expire (Every 30 Minutes)

Update `init_credentials.bat` with new credentials and run:

```bash
init_credentials.bat
```

Or manually:

```bash
python setup_credentials.py
# Choose option 4 to refresh
```

## Load Historical Data

To load 3 months of historical data from s3://edna-dev-meraki-webhooks/:

```bash
python load_historical_data.py
```

This will:
- List all files in source bucket
- Ask for confirmation
- Process and insert into Redshift
- Show progress and summary

## Need Help?

1. **Full Documentation**: See `DEPLOYMENT_GUIDE.md`
2. **Project Overview**: See `PROJECT_SUMMARY.md`
3. **Check Status**: Run `python check_status.py`
4. **Test Webhook**: Run `python test_webhook.py`

## File Locations

- **Local**: `c:\Users\cesta\OneDrive\Documents\GitHub\sa-stuff\meraki-webhook-streaming\`
- **Raw Storage**: `s3://meraki-webhooks-raw-309820967897/raw/`
- **Backup**: `s3://meraki-webhooks-backup-309820967897/firehose-backup/`
- **Source Data**: `s3://edna-dev-meraki-webhooks/webhook-data/`
- **Redshift**: `edna_stream_meraki` schema in `talent_acquisition` database

## Architecture at a Glance

```
┌─────────────┐
│   Meraki    │ Sends webhooks
│  Dashboard  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │ Receives POST requests
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Lambda         │ Flattens & routes
└──────┬──────────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│  S3 Raw     │    │  Firehose   │
│  Storage    │    │  Stream     │
└─────────────┘    └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Redshift   │
                   │  edna_stream│
                   │  _meraki    │
                   └─────────────┘
```

## Key Commands

```bash
# Initialize credentials
init_credentials.bat

# Complete setup
quick_start.bat

# Check status
python check_status.py

# Test webhook
python test_webhook.py

# Load historical data
python load_historical_data.py

# Refresh credentials
python setup_credentials.py
```

## What Gets Created

| AWS Resource | Name |
|--------------|------|
| API Gateway | meraki-webhook-api |
| Lambda | meraki-webhook-processor |
| Firehose | meraki-redshift-stream |
| S3 Bucket (Raw) | meraki-webhooks-raw-309820967897 |
| S3 Bucket (Backup) | meraki-webhooks-backup-309820967897 |
| IAM Roles | MerakiLambdaRole, MerakiFirehoseRole |
| Redshift Schema | edna_stream_meraki |
| Redshift Table | meraki_webhooks |
| Redshift Views | recent_alerts, temperature_alerts |

## Cost

~$14/month for 10,000 webhooks/day

## Success Checklist

- [ ] Dependencies installed
- [ ] Credentials initialized
- [ ] AWS infrastructure deployed
- [ ] Redshift schema created
- [ ] Webhook tested successfully
- [ ] Meraki configured
- [ ] Data appearing in S3
- [ ] Data appearing in Redshift
- [ ] Historical data loaded (optional)

## Next Steps After Setup

1. Monitor CloudWatch Logs for first few webhooks
2. Create Redshift views for analytics
3. Set up CloudWatch alarms for failures
4. Document Meraki webhook configuration
5. Schedule credential refresh reminders
6. Load historical data if needed

## Troubleshooting

### No Data in Redshift

1. Check Lambda logs for errors
2. Verify Firehose delivery status
3. Check S3 backup bucket
4. Confirm table exists in Redshift

### Credentials Expired

```bash
python setup_credentials.py
# Choose option 4 to refresh
```

### Lambda Timeout

Increase timeout in `config.json` and redeploy.

### SSH Tunnel Issues

```bash
ssh -L 5439:edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com:5439 chris.cestari@44.207.39.121
```

## Differences from Greenhouse Project

| Aspect | Greenhouse | Meraki |
|--------|-----------|--------|
| Tables | 83 tables | 1 flexible table |
| Processing | SQS + Batch | Direct Firehose |
| Raw Storage | No | Yes (S3) |
| Schema | Fixed | Flexible (nullable columns) |
| Complexity | High | Medium |

## Sample Queries

```sql
-- Alert summary by type
SELECT 
    alert_type,
    COUNT(*) as count,
    MIN(occurred_at) as first_seen,
    MAX(occurred_at) as last_seen
FROM edna_stream_meraki.meraki_webhooks
GROUP BY alert_type
ORDER BY count DESC;

-- Temperature trends
SELECT 
    device_name,
    DATE_TRUNC('hour', occurred_at) as hour,
    AVG(trigger_sensor_value) as avg_temp_celsius,
    MIN(trigger_sensor_value) as min_temp_celsius,
    MAX(trigger_sensor_value) as max_temp_celsius
FROM edna_stream_meraki.meraki_webhooks
WHERE trigger_type = 'temperature'
  AND occurred_at >= CURRENT_DATE - 7
GROUP BY device_name, hour
ORDER BY device_name, hour;

-- Device health
SELECT 
    device_name,
    device_model,
    network_name,
    COUNT(*) as alert_count,
    MAX(occurred_at) as last_alert
FROM edna_stream_meraki.meraki_webhooks
WHERE occurred_at >= CURRENT_DATE - 7
GROUP BY device_name, device_model, network_name
ORDER BY alert_count DESC;
```

---

**Ready to start?** Run `quick_start.bat` and follow the prompts!
