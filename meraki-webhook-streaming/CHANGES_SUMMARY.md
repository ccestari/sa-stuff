# Changes Summary - Meraki Webhook Streaming

## Overview

Updated the Meraki webhook streaming project with production configuration, flexible schema handling, and historical data migration capabilities.

## Key Changes

### 1. Production Configuration

**config.json updates:**
- ✅ Database: `talent_acquisition` → `db02`
- ✅ Schema: `edna_stream_meraki` (unchanged)
- ✅ S3 Bucket: `meraki-webhooks-raw-*` → `edna-stream-meraki`
- ✅ Added: `cluster_arn`, `ssh_host`, `ssh_user`
- ✅ Added: `source_account` for nonproduction

### 2. Credentials Management

**New file: credentials.yaml** (gitignored)
```yaml
production:
  aws_access_key_id: ASIA...
  aws_secret_access_key: [hidden]
  aws_session_token: [hidden]
  account_id: "309820967897"

nonproduction:
  aws_access_key_id: ASIA...
  aws_secret_access_key: [hidden]
  aws_session_token: [hidden]
  account_id: "205372355929"

redshift:
  password: YOUR_PASSWORD

ssh:
  password: YOUR_SSH_PASSWORD
```

### 3. Lambda Enhancements

**lambda_function.py updates:**

✅ **Schema Detection:**
```python
def detect_schema_version(payload):
    """Detect schema version based on field presence"""
    if 'version' in payload and payload.get('version') == '0.1':
        return 'v0.1'
    required_fields = ['organizationId', 'networkId', 'deviceSerial', 'alertType']
    if all(field in payload for field in required_fields):
        return 'v0.1'
    return 'unknown'
```

✅ **Unknown Schema Alerting:**
```python
def alert_unknown_schema(payload):
    """Alert on unknown schema via CloudWatch Logs and SNS"""
    print(f"⚠️ UNKNOWN SCHEMA DETECTED: {json.dumps(payload, indent=2)}")
    # Sends SNS notification if ALERT_SNS_TOPIC configured
```

✅ **Processing Error Alerting:**
```python
def alert_processing_error(payload, error_msg):
    """Alert on processing errors"""
    print(f"❌ PROCESSING ERROR: {error_msg}")
    # Sends SNS notification if ALERT_SNS_TOPIC configured
```

✅ **Environment Variables:**
- `RAW_BUCKET` - Replaces hardcoded `meraki-webhooks-raw-309820967897`
- `FIREHOSE_STREAM_NAME` - Replaces hardcoded `meraki-redshift-stream`
- `ALERT_SNS_TOPIC` - Optional SNS topic for alerts

### 4. New Scripts

**analyze_historical_data.py:**
- Connects to nonproduction S3
- Analyzes 3 months of webhook data
- Identifies schema variations
- Counts field presence
- Tracks alert types and trigger types
- Saves sample payloads to `schema_samples.json`

**copy_historical_data.py:**
- Copies data from nonproduction to production
- Source: `s3://edna-dev-meraki-webhooks/webhook-data/`
- Destination: `s3://edna-stream-meraki/historical/`
- Shows progress and handles errors

**run_analysis.bat:**
- Automated workflow script
- Runs analysis → copy → schema setup

### 5. Updated Scripts

**setup_redshift_schema.py:**
- ✅ Reads credentials from `credentials.yaml`
- ✅ Uses config values for SSH host/user
- ✅ Connects to `db02` database
- ✅ Creates schema in correct database

**deploy_infrastructure.py:**
- ✅ Uses `edna-stream-meraki` bucket
- ✅ Sets environment variables in Lambda
- ✅ Configures proper IAM permissions

### 6. Documentation

**New files:**
- `SETUP_INSTRUCTIONS.md` - Step-by-step setup guide
- `CHANGES_SUMMARY.md` - This file

**Updated files:**
- `.gitignore` - Added `credentials.yaml`, `schema_samples.json`

## Workflow

### Phase 1: Analysis
```bash
python analyze_historical_data.py
```
- Analyzes historical data for schema variations
- Outputs field statistics and recommendations
- Saves sample payloads

### Phase 2: Migration
```bash
python copy_historical_data.py
```
- Copies historical data to production S3
- Preserves all webhook payloads

### Phase 3: Setup
```bash
python setup_redshift_schema.py
```
- Creates schema in db02
- Creates flexible table structure
- Creates analytical views

### Phase 4: Deploy
```bash
python deploy_infrastructure.py
```
- Deploys Lambda with enhanced error handling
- Creates API Gateway endpoint
- Sets up Firehose stream

### Phase 5: Test
```bash
python test_webhook.py
```
- Tests webhook endpoint
- Verifies data flow

## Schema Flexibility Features

### 1. Version Detection
Lambda detects schema version and handles accordingly:
- v0.1: Current schema (version field present)
- unknown: Missing required fields or new structure

### 2. Graceful Degradation
- Continues processing even with unknown schemas
- Uses best-effort flattening
- Logs warnings for investigation

### 3. Alerting
- CloudWatch Logs: All schema issues logged
- SNS Notifications: Optional alerts to email/SMS
- Error tracking: Processing errors captured

### 4. Nullable Fields
All fields except metadata are nullable in Redshift:
- Handles missing fields gracefully
- No data loss on schema variations
- Raw JSON preserved for reference

## Environment Variables

### Lambda Configuration

Required:
```
FIREHOSE_STREAM_NAME=meraki-redshift-stream
RAW_BUCKET=edna-stream-meraki
```

Optional:
```
ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:309820967897:meraki-webhook-alerts
```

## Security Updates

### Credentials
- ✅ All credentials in `credentials.yaml` (gitignored)
- ✅ No hardcoded passwords in code
- ✅ No credentials in config.json
- ✅ Environment-based credential loading

### IAM
- ✅ Least privilege policies
- ✅ Explicit resource ARNs
- ✅ No wildcard permissions

## Testing Checklist

- [ ] Run `analyze_historical_data.py` - Check schema variations
- [ ] Review `schema_samples.json` - Verify payload structures
- [ ] Run `copy_historical_data.py` - Migrate data to production
- [ ] Run `setup_redshift_schema.py` - Create db02 schema
- [ ] Verify schema in Redshift: `SELECT * FROM db02.edna_stream_meraki.meraki_webhooks LIMIT 1;`
- [ ] Run `deploy_infrastructure.py` - Deploy AWS resources
- [ ] Run `test_webhook.py` - Test endpoint
- [ ] Check CloudWatch Logs - Verify logging
- [ ] Query Redshift - Verify data ingestion
- [ ] Test unknown schema - Verify alerting

## Next Steps

1. **Run Analysis:**
   ```bash
   python analyze_historical_data.py
   ```
   Review output for schema variations

2. **Update Lambda if Needed:**
   Based on analysis, update `flatten_meraki_payload()` function

3. **Migrate Data:**
   ```bash
   python copy_historical_data.py
   ```

4. **Deploy:**
   ```bash
   python setup_redshift_schema.py
   python deploy_infrastructure.py
   ```

5. **Configure SNS (Optional):**
   - Create SNS topic for alerts
   - Add email/SMS subscriptions
   - Update Lambda environment variable

6. **Monitor:**
   - Check CloudWatch Logs for schema issues
   - Review SNS alerts
   - Query Redshift for data quality

## Rollback Plan

If issues occur:

1. **Revert config.json:**
   - Change database back to `talent_acquisition`
   - Change bucket back to original

2. **Revert Lambda:**
   - Deploy previous version without schema detection

3. **Data Recovery:**
   - Historical data preserved in nonproduction
   - Raw payloads in S3 for reprocessing

## Support

For issues:
1. Check `SETUP_INSTRUCTIONS.md`
2. Review CloudWatch Logs
3. Check `schema_samples.json` for payload examples
4. Verify credentials in `credentials.yaml`
