# Claude AI Deployment Prompt - Meraki Webhook Streaming

## Project Context

You are helping deploy a **Meraki Webhook Streaming to Redshift** system that:

1. **Receives** Meraki webhooks via API Gateway
2. **Stores** raw JSON payloads to S3 for archival
3. **Flattens** varying webhook structures to consistent Redshift schema
4. **Streams** data to Redshift via Kinesis Firehose
5. **Handles** 24+ alert types with flexible schema

## Architecture

```
Meraki Dashboard
    ↓ (webhook)
API Gateway
    ↓
Lambda (flatten + route)
    ↓
    ├→ S3 (raw storage)
    └→ Firehose → Redshift (edna_stream_meraki.meraki_webhooks)
```

## Current Implementation Status

### ✅ Completed
- **Historical Data Analysis**: Analyzed 3,336 files from s3://edna-dev-meraki-webhooks/webhook-data/
  - Identified 24+ alert types (74% "Sensor change detected", plus Power, Motion, Geofencing, APs, Clients, etc.)
  - Detected schema variations and edge cases
  - 1 record with missing required fields (has key1/key2/key3 instead)
- **Configuration**: Updated config.json for production (db02 database, edna-stream-meraki bucket)
- **Credentials**: Created credentials.yaml with multi-environment support (gitignored)
- **Lambda Function**: Enhanced with schema version detection, unknown schema alerting, flexible payload handling
- **Infrastructure Deployment**: deploy_infrastructure.py ready (NOT YET RUN)
- **Redshift Schema**: setup_redshift_schema.py ready with flexible schema supporting 24+ alert types (NOT YET RUN - requires VPN)
- **Testing**: test_webhook.py ready
- **Historical Data Copy**: copy_historical_data.py ready (3,336 files)

### 🔄 Next Steps

**On Mac (VPN required - one time):**
1. Clone repo, install dependencies, create credentials.yaml
2. Connect to VPN
3. Run: `python setup_redshift_schema.py`
4. Commit/push any changes

**On Windows (return here after VPN tasks):**
1. Pull latest changes
2. Run: `python deploy_infrastructure.py`
3. Run: `python test_webhook.py`
4. Configure Meraki Dashboard with API Gateway URL
5. Optional: `python copy_historical_data.py` (3,336 files)

See WORKFLOW.md for detailed step-by-step instructions.

## Key Files

### Core Processing
- `lambda_function.py` - Webhook processing with flexible flattening, schema detection, alerting
- `flatten_meraki_payload()` - Handles varying alert structures
- `detect_schema_version()` - Identifies schema version
- `alert_unknown_schema()` - CloudWatch/SNS alerts for unknown schemas
- `alert_processing_error()` - Error handling and alerting

### Configuration
- `config.json` - AWS resources, Redshift, S3, Firehose settings (db02, edna-stream-meraki)
- `credentials.yaml` - Multi-environment credentials (gitignored)

### Deployment
- `deploy_infrastructure.py` - Creates all AWS resources
- `setup_redshift_schema.py` - Creates flexible Redshift schema (requires VPN)

### Analysis & Data
- `analyze_historical_data.py` - Analyzed 3,336 historical files
- `copy_historical_data.py` - Copy historical data from nonproduction to production

### Testing
- `test_webhook.py` - End-to-end webhook testing

## Alert Types Identified (from Historical Data Analysis)

**24+ alert types found in 3,336 historical files:**
- **Sensor change detected** (74% of all alerts) - temperature, humidity, water, door, motion
- **Power supply went down** / **Power supply came back online**
- **Motion detected** / **Motion has stopped**
- **Geofencing in** / **Geofencing out**
- **APs went down** / **APs came up**
- **Clients were connected** / **Clients were disconnected**
- **Gateway went down** / **Gateway came back online**
- **Uplink status changed**
- **Settings changed**
- **Rogue AP detected**
- **Malware detected**
- And more...

**Schema Variations:**
- Most records follow v0.1 schema with standard fields
- 1 edge case record with key1/key2/key3 instead of standard fields
- Flexible schema with nullable columns handles all variations

## Flexible Schema Design

The Redshift table handles varying payloads:

```sql
CREATE TABLE edna_stream_meraki.meraki_webhooks (
    -- Metadata (always present)
    id, ingestion_timestamp, timestamp, source, lambda_request_id,
    
    -- Base webhook fields (always present)
    version, organization_id, network_id, device_serial, device_name,
    alert_id, alert_type, alert_level, occurred_at,
    
    -- Alert data (varies by type)
    alert_config_id, alert_config_name, started_alerting,
    
    -- Trigger data (varies by alert type)
    trigger_type, trigger_sensor_value, trigger_node_id,
    
    -- Raw payload for reference
    payload_json
);
```

All fields except metadata are nullable to handle variations.

## Configuration

### AWS Resources
- **Production Account**: 309820967897 (deployment target)
- **Nonproduction Account**: 205372355929 (historical data source)
- **Region**: us-east-1
- **Redshift**: edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com
- **Database**: db02 (CHANGED from talent_acquisition)
- **Schema**: edna_stream_meraki
- **Redshift User**: ccestari
- **SSH Bastion**: 44.207.39.121 (user: chris.cestari)

### S3 Buckets
- **Single Bucket**: edna-stream-meraki (used for both raw and backup)
- **Historical Source**: s3://edna-dev-meraki-webhooks/webhook-data/ (3,336 files in nonproduction account)

### Lambda
- **Function**: meraki-webhook-processor
- **Runtime**: Python 3.9
- **Memory**: 512 MB
- **Timeout**: 60 seconds
- **Environment Variables**:
  - FIREHOSE_STREAM_NAME: meraki-redshift-stream
  - RAW_BUCKET: edna-stream-meraki
  - ALERT_SNS_TOPIC: (optional for alerting)

### Firehose
- **Stream**: meraki-redshift-stream
- **Buffer**: 5 MB or 300 seconds
- **Destination**: S3 (backup)

## Important Notes

- **VPN REQUIRED**: Must be on company VPN to connect to SSH bastion host (44.207.39.121)
- **AWS Credentials**: Rotate every 30 minutes - stored in credentials.yaml (gitignored)
- **SSH Tunnel**: Required for Redshift access via bastion host (port 5439)
- **Flexible Schema**: Single table handles 24+ alert types with nullable columns
- **Raw Storage**: All payloads stored to S3 before processing
- **Error Handling**: Unknown schema alerting via CloudWatch/SNS, graceful fallback
- **Batch Processing**: Firehose buffers 5MB or 300 seconds
- **Historical Data**: 3,336 files analyzed, ready to copy from nonproduction to production

## Credentials Management

**IMPORTANT**: credentials.yaml is gitignored and contains:
- AWS credentials for production (309820967897) and nonproduction (205372355929)
- Redshift password
- SSH password

**AWS credentials expire every 30 minutes** - must be refreshed from AWS SSO:
- SSO start URL: https://d-9067640efb.awsapps.com/start/#
- SSO Region: us-east-1
- Production: 309820967897_AWSAdministratorAccess
- Nonproduction: 205372355929_AWSAdministratorAccess

Update credentials.yaml with fresh credentials before deployment.

## Troubleshooting

### Credentials Expired
Update credentials.yaml with fresh credentials from AWS SSO.

### SSH Tunnel (Manual)
```bash
# Must be on VPN first!
ssh chris.cestari@44.207.39.121
# Or with port forwarding:
ssh -L 5439:edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com:5439 chris.cestari@44.207.39.121
```

### Test Webhook
```bash
python test_webhook.py --count 5
```

### Check Logs
```bash
# Lambda logs
aws logs tail /aws/lambda/meraki-webhook-processor --follow

# Firehose logs
aws logs tail /aws/kinesisfirehose/meraki-redshift-stream --follow
```

## Deployment Checklist

- [x] Historical data analyzed (3,336 files, 24+ alert types)
- [x] Configuration updated (db02, edna-stream-meraki)
- [x] Credentials file created (credentials.yaml - gitignored)
- [x] Lambda enhanced with schema detection and alerting
- [x] Flexible Redshift schema designed
- [ ] **VPN connection established**
- [ ] AWS credentials valid (rotate every 30 min)
- [ ] Python dependencies installed (paramiko==2.12.0, sshtunnel==0.4.0)
- [ ] Redshift schema created (requires VPN)
- [ ] Infrastructure deployed
- [ ] Webhook tested successfully
- [ ] Meraki Dashboard configured
- [ ] CloudWatch logs accessible
- [ ] Historical data loaded (optional - 3,336 files)

## Completed Analysis & Scripts

1. **Historical Data Analysis** ✅
   - analyze_historical_data.py - Analyzed 3,336 files
   - Identified 24+ alert types and schema variations
   - Generated schema_samples.json with examples

2. **Historical Data Copy** ✅
   - copy_historical_data.py - Ready to copy 3,336 files
   - Cross-account copy from nonproduction to production

3. **Schema Enhancements** ✅
   - Flexible schema with nullable columns
   - Handles all 24+ alert types
   - Views: recent_alerts, temperature_alerts

4. **Lambda Enhancements** ✅
   - detect_schema_version() - Identifies schema version
   - alert_unknown_schema() - CloudWatch/SNS alerts
   - alert_processing_error() - Error handling
   - Environment variables for configuration

## Future Enhancements

1. **Monitoring**
   - CloudWatch alarms for failures
   - SNS topic configuration
   - Daily summary reports

2. **Analytics**
   - Temperature trends by device
   - Alert frequency by type
   - Device health dashboard

3. **Data Quality**
   - Webhook signature validation
   - Duplicate detection
   - Data quality checks

## Platform Compatibility

**Windows**: All Python scripts work as-is
**macOS**: All Python scripts work as-is (no Windows-specific commands used)

## Reference Documentation

- **Meraki Webhooks**: https://developer.cisco.com/meraki/webhooks/
- **Postman Collection**: https://documenter.getpostman.com/view/897512/SVfRtnU7
- **AWS Firehose**: https://docs.aws.amazon.com/firehose/
- **Redshift COPY**: https://docs.aws.amazon.com/redshift/latest/dg/r_COPY.html

This system provides a flexible, scalable solution for streaming Meraki webhook data to Redshift while maintaining raw data for audit and reprocessing.
