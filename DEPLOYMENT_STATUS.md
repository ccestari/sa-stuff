# Deployment Status

## ✅ Schema Analysis - MATCHES PERFECTLY

The SQL queries you ran match the deployment scripts exactly:

### Table Structure ✅
- All columns match between SQL and lambda_function.py
- Nullable columns correctly handle 24+ alert types
- IDENTITY primary key, timestamps, metadata fields all present
- Raw payload_json field for audit trail

### Views ✅
- `recent_alerts` - Last 7 days of alerts
- `temperature_alerts` - Temperature-specific with C/F conversion

### Permissions ✅
- Schema usage granted to PUBLIC
- SELECT granted on all tables

## Current Status

### ✅ Completed
1. **Redshift Schema Created** (via SQL queries on Mac)
   - Table: edna_stream_meraki.meraki_webhooks
   - Views: recent_alerts, temperature_alerts
   - Permissions: Granted

2. **Code Ready**
   - Lambda function matches schema
   - Config points to db02 database
   - All scripts tested

3. **Git Repository Clean**
   - No credentials committed
   - Pushed to remote successfully

### 🔄 Next Steps

**Before deploying, sync changes from Mac:**

1. **Pull from remote** (if you made changes on Mac):
   ```bash
   cd c:\Users\cesta\source\repos\sa-stuff\meraki-webhook-streaming
   git pull origin main
   ```

2. **Update credentials.yaml** (if expired):
   - AWS credentials expire every 30 minutes
   - Update with fresh credentials from AWS SSO

3. **Deploy infrastructure**:
   ```bash
   python deploy_infrastructure.py
   ```
   
   This creates:
   - S3 bucket: edna-stream-meraki
   - Lambda: meraki-webhook-processor
   - API Gateway: meraki-webhook-api
   - Firehose: meraki-redshift-stream
   - IAM roles

4. **Test webhook**:
   ```bash
   python test_webhook.py
   ```

5. **Configure Meraki Dashboard**:
   - Use API Gateway URL from deployment output

## Folder Structure Status

### ✅ Correct Location
- `c:\Users\cesta\source\repos\sa-stuff\meraki-webhook-streaming\` ✅

### ⚠️ OneDrive Duplicates (Should NOT be used)
- `c:\Users\cesta\OneDrive\Documents\GitHub\sa-stuff\greenhouse-webhook-streaming\` ⚠️
- `c:\Users\cesta\OneDrive\Documents\GitHub\sa-stuff\meraki-webhook-streaming\` ⚠️

**Action**: Always work in `c:\Users\cesta\source\repos\sa-stuff\` (git repo location)

## Schema Verification

### Lambda flatten_meraki_payload() Output:
```python
{
    'version', 'shared_secret', 'sent_at',
    'organization_id', 'organization_name', 'organization_url',
    'network_id', 'network_name', 'network_url', 'network_tags',
    'device_serial', 'device_mac', 'device_name', 'device_url', 'device_tags', 'device_model',
    'alert_id', 'alert_type', 'alert_type_id', 'alert_level', 'occurred_at',
    'alert_config_id', 'alert_config_name', 'started_alerting',
    'condition_id', 'trigger_ts', 'trigger_type', 'trigger_node_id', 'trigger_sensor_value'
}
```

### Redshift Table Columns:
```sql
-- Metadata
id, ingestion_timestamp, timestamp, source, lambda_request_id, environment, s3_raw_location,
-- Base webhook fields  
version, shared_secret, sent_at,
organization_id, organization_name, organization_url,
network_id, network_name, network_url, network_tags,
-- Device information
device_serial, device_mac, device_name, device_url, device_tags, device_model,
-- Alert information
alert_id, alert_type, alert_type_id, alert_level, occurred_at,
-- Alert data
alert_config_id, alert_config_name, started_alerting,
-- Trigger data
condition_id, trigger_ts, trigger_type, trigger_node_id, trigger_sensor_value,
-- Raw payload
payload_json
```

### ✅ Perfect Match
- All Lambda output fields have corresponding Redshift columns
- Metadata fields added by Lambda (timestamp, source, lambda_request_id, etc.)
- All columns nullable except metadata (handles schema variations)

## Ready to Deploy?

- [x] Redshift schema created
- [x] Schema matches Lambda function
- [x] Config points to correct database (db02)
- [x] Git repository clean
- [ ] Pull latest changes from Mac (if any)
- [ ] AWS credentials valid
- [ ] Run deploy_infrastructure.py
- [ ] Test webhook
- [ ] Configure Meraki Dashboard

## Commands Summary

```bash
# 1. Pull changes (if made on Mac)
git pull origin main

# 2. Deploy infrastructure
python deploy_infrastructure.py

# 3. Test
python test_webhook.py

# 4. Optional: Load historical data
python copy_historical_data.py
```
