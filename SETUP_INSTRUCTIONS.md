# Setup Instructions - Updated for Production

## Prerequisites

1. **Credentials file created**: `credentials.yaml` (already created with your credentials)
2. **Python environment**: Conda/Anaconda with required packages
3. **SSH access**: To bastion host for Redshift

## Step-by-Step Setup

### 1. Analyze Historical Data

This identifies schema variations in the 3 months of historical data:

```bash
python analyze_historical_data.py
```

**What it does:**
- Connects to nonproduction S3 bucket
- Analyzes webhook payloads for field variations
- Identifies alert types and trigger types
- Saves sample payloads to `schema_samples.json`
- Provides recommendations for Lambda updates

**Expected output:**
- Total records analyzed
- Field presence percentages
- Alert type distribution
- Trigger type distribution
- Schema variation warnings

### 2. Copy Historical Data to Production

Copies data from nonproduction to production S3:

```bash
python copy_historical_data.py
```

**What it does:**
- Lists all files in `s3://edna-dev-meraki-webhooks/webhook-data/`
- Copies to `s3://edna-stream-meraki/historical/`
- Shows progress and summary

### 3. Setup Redshift Schema

Creates schema in db02 database:

```bash
python setup_redshift_schema.py
```

**What it does:**
- Establishes SSH tunnel to Redshift
- Creates `edna_stream_meraki` schema in `db02` database
- Creates `meraki_webhooks` table with flexible schema
- Creates views: `recent_alerts`, `temperature_alerts`
- Grants permissions

### 4. Deploy Infrastructure

```bash
python deploy_infrastructure.py
```

**What it does:**
- Creates S3 bucket: `edna-stream-meraki`
- Creates Lambda with updated code (schema detection + alerting)
- Creates API Gateway
- Creates Firehose stream
- Creates IAM roles

### 5. Test Webhook

```bash
python test_webhook.py
```

## Key Changes Made

### 1. Configuration Updates

**config.json:**
- Database changed to `db02`
- S3 bucket changed to `edna-stream-meraki`
- Added SSH configuration from config

### 2. Credentials Management

**credentials.yaml** (gitignored):
- Production AWS credentials
- Nonproduction AWS credentials
- Redshift password
- SSH password

### 3. Lambda Enhancements

**lambda_function.py:**
- Schema version detection
- Unknown schema alerting (CloudWatch + SNS)
- Processing error alerting
- Environment variables instead of hardcoded values
- Flexible field handling

### 4. New Scripts

- `analyze_historical_data.py` - Analyze schema variations
- `copy_historical_data.py` - Copy nonprod → prod
- `run_analysis.bat` - Run all steps

## Environment Variables for Lambda

Set these in Lambda configuration:

```
FIREHOSE_STREAM_NAME=meraki-redshift-stream
RAW_BUCKET=edna-stream-meraki
ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:309820967897:meraki-webhook-alerts (optional)
```

## Schema Flexibility

The Lambda now:
1. Detects schema version based on fields present
2. Handles missing/nullable fields gracefully
3. Alerts on unknown schemas via CloudWatch Logs
4. Sends SNS notifications if topic configured
5. Continues processing with best-effort flattening

## Next Steps After Analysis

1. Review `schema_samples.json` for payload variations
2. Update Lambda if new fields discovered
3. Update Redshift schema if needed
4. Deploy updated Lambda
5. Configure SNS topic for alerts (optional)

## Troubleshooting

### Credentials Expired

Edit `credentials.yaml` with fresh credentials from AWS SSO.

### SSH Tunnel Issues

Verify SSH password in `credentials.yaml` and bastion host accessibility.

### Schema Variations

Check `schema_samples.json` and CloudWatch Logs for unknown schemas.

## Running Commands

Use your conda environment:

```bash
# Activate conda environment if needed
conda activate base

# Run scripts
python analyze_historical_data.py
python copy_historical_data.py
python setup_redshift_schema.py
python deploy_infrastructure.py
```

Or use the batch script:

```bash
run_analysis.bat
```
