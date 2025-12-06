# Claude AI Deployment Prompt - Meraki Webhook Streaming

**Last Updated**: 2025-12-06

## Project Overview

Stream Meraki webhook data to Redshift for analytics. System receives webhooks via API Gateway, processes with Lambda, stores raw JSON to S3, and syncs to Redshift every 5 minutes.

## Current Architecture (WORKING)

```
Meraki Dashboard
    ↓ (webhook)
API Gateway: https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook
    ↓
Lambda: meraki-webhook-processor
    ├→ S3: s3://edna-stream-meraki/raw/ (immediate)
    └→ CloudWatch Logs
         ↓
    (every 5 min via sync script)
         ↓
Redshift: edna_stream_meraki.meraki_webhooks
```

## What's Working ✅

- API Gateway receiving webhooks
- Lambda processing and flattening payloads
- Raw JSON stored to S3 for audit trail
- Redshift schema with 37 flexible columns
- Manual/scheduled COPY from S3 to Redshift
- 11+ webhooks successfully processed

## What's NOT Working ❌

- Firehose → Redshift (cluster not accessible)
- Automatic real-time loading (5 min delay via sync)

## Why Firehose Doesn't Work

**Root Cause**: Redshift cluster (`edna-prod-dw`) is behind VPN/bastion and not publicly accessible. Firehose requires direct network access to Redshift.

**Attempted Solutions**:
1. ❌ Firehose with RedshiftDestinationConfiguration - Can't connect
2. ❌ IAM role for COPY - Role not associated with cluster  
3. ✅ Manual COPY with user credentials - Works!
4. ✅ Scheduled sync script via SSH tunnel - Works!

## Current Solution

### On Windows (Development)
```bash
python check_s3_data.py  # Monitor S3
python check_lambda_logs.py  # Check Lambda
python test_webhook.py  # Send test webhooks
```

### On macOS (Production - VPN Required)
```bash
python sync_s3_to_redshift.py
# Or
./sync_s3_to_redshift.sh
```

Runs COPY command every 5 minutes to sync S3 → Redshift.

## AWS Resources

### Account & Region
- **Account**: 309820967897
- **Region**: us-east-1

### API Gateway
- **URL**: https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook
- **Stage**: prod
- **Method**: POST /webhook

### Lambda
- **Function**: meraki-webhook-processor
- **Runtime**: Python 3.9
- **Memory**: 512 MB
- **Timeout**: 60 seconds
- **Environment Variables**:
  - `RAW_BUCKET`: edna-stream-meraki
  - `FIREHOSE_STREAM_NAME`: meraki-redshift-stream (not used)

### S3
- **Bucket**: edna-stream-meraki
- **Raw webhooks**: `raw/YYYY-MM-DD-HH-MM-SS-{request_id}.json`
- **Firehose backup**: `firehose-backup/` (legacy, not used)

### Redshift
- **Cluster**: edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com
- **Port**: 5439
- **Database**: db02
- **Schema**: edna_stream_meraki
- **Table**: meraki_webhooks (37 columns)
- **Access**: Via SSH tunnel through bastion (44.207.39.121)

### IAM Roles
- **Lambda Role**: MerakiLambdaRole
- **Firehose Role**: MerakiFirehoseRole (not used for Redshift)

## Redshift Schema

```sql
CREATE TABLE edna_stream_meraki.meraki_webhooks (
    -- Metadata
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ingestion_timestamp TIMESTAMP DEFAULT GETDATE(),
    timestamp VARCHAR(50),
    source VARCHAR(50),
    lambda_request_id VARCHAR(100),
    environment VARCHAR(50),
    s3_raw_location VARCHAR(500),
    
    -- Base webhook fields
    version VARCHAR(10),
    shared_secret VARCHAR(100),
    sent_at TIMESTAMP,
    organization_id VARCHAR(50),
    organization_name VARCHAR(200),
    organization_url VARCHAR(500),
    network_id VARCHAR(100),
    network_name VARCHAR(200),
    network_url VARCHAR(500),
    network_tags VARCHAR(1000),
    
    -- Device information
    device_serial VARCHAR(50),
    device_mac VARCHAR(50),
    device_name VARCHAR(200),
    device_url VARCHAR(500),
    device_tags VARCHAR(1000),
    device_model VARCHAR(50),
    
    -- Alert information
    alert_id VARCHAR(100),
    alert_type VARCHAR(200),
    alert_type_id VARCHAR(100),
    alert_level VARCHAR(50),
    occurred_at TIMESTAMP,
    
    -- Alert data
    alert_config_id BIGINT,
    alert_config_name VARCHAR(200),
    started_alerting BOOLEAN,
    
    -- Trigger data
    condition_id BIGINT,
    trigger_ts DOUBLE PRECISION,
    trigger_type VARCHAR(50),
    trigger_node_id BIGINT,
    trigger_sensor_value DOUBLE PRECISION,
    
    -- Raw payload
    payload_json VARCHAR(MAX)
);
```

## COPY Command (Manual Load)

Run in Redshift Query Editor v2:

```sql
COPY edna_stream_meraki.meraki_webhooks (
    timestamp, source, lambda_request_id, environment, s3_raw_location,
    version, shared_secret, sent_at,
    organization_id, organization_name, organization_url,
    network_id, network_name, network_url, network_tags,
    device_serial, device_mac, device_name, device_url, device_tags, device_model,
    alert_id, alert_type, alert_type_id, alert_level, occurred_at,
    alert_config_id, alert_config_name, started_alerting,
    condition_id, trigger_ts, trigger_type, trigger_node_id, trigger_sensor_value,
    payload_json
)
FROM 's3://edna-stream-meraki/raw/'
ACCESS_KEY_ID '<your_access_key>'
SECRET_ACCESS_KEY '<your_secret_key>'
SESSION_TOKEN '<your_session_token>'
JSON 'auto'
TIMEFORMAT 'auto'
REGION 'us-east-1'
TRUNCATECOLUMNS
BLANKSASNULL
EMPTYASNULL;
```

## Key Files

### Core Processing
- `lambda_function.py` - Webhook processor with flexible flattening
- `setup_redshift_schema.py` - Creates Redshift schema and table

### Sync & Load
- `sync_s3_to_redshift.py` - Automated sync (Python, VPN required)
- `sync_s3_to_redshift.sh` - Automated sync (Shell, macOS/Linux)
- `load_s3_to_redshift.py` - One-time load (VPN required)

### Deployment
- `deploy_infrastructure.py` - Deploys all AWS resources
- `recreate_firehose_redshift.py` - Recreate Firehose (not needed)

### Monitoring
- `check_s3_data.py` - Check S3 files
- `check_lambda_logs.py` - Check Lambda CloudWatch logs
- `check_status.py` - Check all infrastructure
- `test_webhook.py` - Send test webhooks

### Configuration
- `config.json` - AWS resources configuration
- `credentials.yaml` - AWS credentials (NOT in git)
- `credentials.yaml.template` - Template for credentials
- `requirements.txt` - Python dependencies

## Setup on New Machine (macOS)

1. **Clone repo**
   ```bash
   git clone <repo-url>
   cd meraki-webhook-streaming
   ```

2. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure credentials**
   ```bash
   cp credentials.yaml.template credentials.yaml
   # Edit with your AWS credentials
   ```

4. **Test connection**
   ```bash
   python3 check_s3_data.py
   ```

5. **Connect to VPN**
   ```bash
   # Connect to VPN to access bastion/Redshift
   ```

6. **Start sync**
   ```bash
   chmod +x sync_s3_to_redshift.sh
   ./sync_s3_to_redshift.sh
   ```

## Credentials Management

### AWS Credentials (Expire every 30 min)
```yaml
production:
  aws_access_key_id: ASIA...
  aws_secret_access_key: ...
  aws_session_token: ...
  account_id: "309820967897"
```

### Redshift & SSH
```yaml
redshift:
  password: Cc@succ123!

ssh:
  password: 1faLp42x7Vf161670!
```

## Sample Webhook Payload

```json
{
  "version": "0.1",
  "organizationId": "25998",
  "networkId": "L_570831252769210967",
  "deviceSerial": "Q3CA-4ZEK-5VUZ",
  "deviceName": "FB-602",
  "alertType": "Sensor change detected",
  "occurredAt": "2025-12-06T02:08:19Z",
  "alertData": {
    "alertConfigName": "Temperature Threshold FB",
    "triggerData": [{
      "trigger": {
        "type": "temperature",
        "sensorValue": 17.0
      }
    }]
  }
}
```

## Alert Types Handled

- **Sensor**: temperature, humidity, water, door, motion
- **Device**: went_down, came_up, power_supply_down
- **Network**: usage_alert, settings_changed
- **Security**: rogue_ap_detected, malware_detected

## Monitoring & Troubleshooting

### Check S3 Files
```bash
python check_s3_data.py
```

### Check Lambda Logs
```bash
python check_lambda_logs.py
```

### Send Test Webhook
```bash
python test_webhook.py --count 5
```

### Query Redshift
```sql
-- Recent alerts
SELECT * FROM edna_stream_meraki.recent_alerts LIMIT 10;

-- Temperature alerts
SELECT * FROM edna_stream_meraki.temperature_alerts;

-- Count by device
SELECT device_name, COUNT(*) 
FROM edna_stream_meraki.meraki_webhooks 
GROUP BY device_name;
```

## Common Issues

### Credentials Expired
AWS credentials expire every 30 minutes. Update `credentials.yaml` with fresh credentials.

### No Data in Redshift
1. Check S3 has files: `python check_s3_data.py`
2. Check Lambda is processing: `python check_lambda_logs.py`
3. Run sync manually: `python sync_s3_to_redshift.py`

### VPN Not Connected
Sync script requires VPN to access bastion/Redshift.

### IAM Role Error
Use personal AWS credentials in COPY command, not IAM role.

## Success Criteria

- ✅ Webhooks received and processed within seconds
- ✅ Raw payloads stored to S3 for audit
- ✅ Data appears in Redshift within 5 minutes
- ✅ All alert types handled correctly
- ✅ Failed records logged to CloudWatch
- ✅ Complete documentation provided
- ⚠️ Near real-time (5 min delay, not instant)

## Future Improvements

1. **Lambda in VPC** - Direct Redshift access without sync script
2. **EventBridge Scheduler** - AWS-native scheduled COPY
3. **Redshift Data API** - Serverless inserts from Lambda
4. **Duplicate Detection** - Prevent re-loading same files
5. **Data Quality Checks** - Validate payloads before insert

## Reference Documentation

- **Meraki Webhooks**: https://developer.cisco.com/meraki/webhooks/
- **AWS Firehose**: https://docs.aws.amazon.com/firehose/
- **Redshift COPY**: https://docs.aws.amazon.com/redshift/latest/dg/r_COPY.html
- **Redshift Data API**: https://docs.aws.amazon.com/redshift-data/

## Project Files

See `FINAL_STATUS.md` for complete system status and `CONVERSATION_LOG.md` for development history.
