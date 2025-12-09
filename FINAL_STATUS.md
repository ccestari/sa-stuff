# Meraki Webhook Streaming - Final Status

**Last Updated**: 2025-12-06

## ✅ Working System

### Architecture
```
Meraki Dashboard
    ↓ (webhook)
API Gateway: https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook
    ↓
Lambda: meraki-webhook-processor
    ↓
S3: s3://edna-stream-meraki/raw/
    ↓ (manual COPY every 5 min)
Redshift: edna_stream_meraki.meraki_webhooks
```

### What's Working
- ✅ API Gateway receiving webhooks
- ✅ Lambda processing and flattening payloads
- ✅ Raw JSON stored to S3 for audit
- ✅ Redshift schema created with 37 columns
- ✅ Manual COPY from S3 to Redshift working

### What's NOT Working
- ❌ Firehose → Redshift (cluster not accessible from Firehose)
- ❌ Automatic data loading (requires manual COPY or scheduled script)

## 🔧 Current Solution

**Manual COPY Command** (run in Redshift Query Editor v2):
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

**Automated Solution** (requires VPN):
```bash
python sync_s3_to_redshift.py
```
Runs COPY command every 5 minutes automatically.

## 📊 Data Flow

1. **Meraki sends webhook** → API Gateway
2. **Lambda receives** → Flattens payload
3. **Lambda writes** → S3 raw/ (immediate)
4. **Manual/Scheduled COPY** → Redshift (every 5 min)

## 🔑 Key Files

### Core Infrastructure
- `lambda_function.py` - Webhook processor
- `setup_redshift_schema.py` - Creates Redshift table
- `deploy_infrastructure.py` - Deploys AWS resources

### Sync Scripts
- `sync_s3_to_redshift.py` - Automated sync (VPN required)
- `load_s3_to_redshift.py` - One-time load (VPN required)

### Monitoring
- `check_s3_data.py` - Check S3 files
- `check_lambda_logs.py` - Check Lambda execution
- `test_webhook.py` - Send test webhooks

### Configuration
- `config.json` - AWS resources config
- `credentials.yaml` - AWS credentials (NOT in git)
- `requirements.txt` - Python dependencies

## 🚀 Setup on New Machine (macOS)

1. **Clone repo**
   ```bash
   git clone <repo-url>
   cd meraki-webhook-streaming
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure credentials**
   ```bash
   cp credentials.yaml.template credentials.yaml
   # Edit credentials.yaml with your AWS credentials
   ```

4. **Test connection**
   ```bash
   python check_s3_data.py
   ```

5. **Start sync** (when on VPN)
   ```bash
   python sync_s3_to_redshift.py
   ```

## 📝 Why Firehose Doesn't Work

**Problem**: Redshift cluster is behind bastion/VPN and not publicly accessible.

**Attempted Solutions**:
1. ❌ Firehose with Redshift destination - Can't connect to cluster
2. ❌ IAM role association - Role not associated with cluster
3. ✅ Manual COPY with user credentials - Works!

**Root Cause**: Firehose requires direct network access to Redshift. Your cluster requires VPN/bastion access.

## 🎯 Recommendations

### Short Term
- Run `sync_s3_to_redshift.py` on work Mac (has VPN access)
- Schedule to run every 5 minutes
- Data will be near real-time (5 min delay)

### Long Term Options
1. **Lambda in VPC** - Configure Lambda to access Redshift via VPC
2. **EventBridge + Lambda** - Scheduled Lambda runs COPY command
3. **Make Redshift public** - Not recommended for security
4. **Keep current** - Manual COPY is simple and works

## 📈 Current Stats

- **Total webhooks processed**: 11+
- **S3 raw files**: 10+ files
- **Redshift records**: 11 (after manual COPY)
- **API Gateway URL**: https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook

## 🔐 Security Notes

- `credentials.yaml` is in `.gitignore` - NEVER commit
- AWS credentials expire every 30 minutes
- Redshift password stored in credentials.yaml
- SSH password for bastion stored in credentials.yaml

## ✅ Success Criteria Met

- ✅ Webhooks received and processed within seconds
- ✅ Raw payloads stored to S3 for audit
- ✅ Data appears in Redshift (via manual COPY)
- ✅ All alert types handled correctly
- ✅ Failed records logged to CloudWatch
- ✅ Complete documentation provided
- ⚠️ Near real-time (5 min delay instead of instant)
