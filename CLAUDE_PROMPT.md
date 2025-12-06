# Claude AI - Meraki Webhook Streaming Project

## Current Status: Ready for Deployment

### ✅ Completed

1. **Analysis Phase**
   - Analyzed 3,336 historical files (120 records sampled)
   - Identified 24 alert types (Sensor, Power, Motion, Geofencing, APs, Clients, etc.)
   - Detected schema variations (1 record with key1/key2/key3 instead of standard fields)
   - Saved sample payloads to `schema_samples.json`

2. **Configuration**
   - `config.json`: Updated for db02 database, edna-stream-meraki bucket
   - `credentials.yaml`: Multi-environment credentials (production + nonproduction)
   - All hardcoded values replaced with config/environment variables

3. **Lambda Function**
   - Schema version detection (`detect_schema_version()`)
   - Unknown schema alerting via CloudWatch + SNS
   - Processing error alerting
   - Flexible field handling for 24+ alert types
   - Environment variables: `FIREHOSE_STREAM_NAME`, `RAW_BUCKET`, `ALERT_SNS_TOPIC`

4. **Scripts Created**
   - `analyze_historical_data.py` - Schema analysis (COMPLETED)
   - `copy_historical_data.py` - Nonprod → Prod migration
   - `setup_redshift_schema.py` - db02 schema creation
   - `deploy_infrastructure.py` - AWS resource deployment
   - `test_webhook.py` - Endpoint testing

5. **Documentation**
   - README.md, DEPLOYMENT_GUIDE.md, SETUP_INSTRUCTIONS.md
   - CHANGES_SUMMARY.md, PROJECT_SUMMARY.md
   - All files in git repo: `c:\Users\cesta\source\repos\sa-stuff\meraki-webhook-streaming`

### 🔄 Next Steps

1. **Copy Historical Data (Optional)**
   ```bash
   python copy_historical_data.py
   ```
   - Copies 3,336 files from nonproduction to production S3
   - Source: `s3://edna-dev-meraki-webhooks/webhook-data/`
   - Destination: `s3://edna-stream-meraki/historical/`

2. **Setup Redshift Schema**
   ```bash
   python setup_redshift_schema.py
   ```
   - Creates schema in db02 database
   - Creates flexible table supporting 24+ alert types
   - Creates views: `recent_alerts`, `temperature_alerts`

3. **Deploy Infrastructure**
   ```bash
   python deploy_infrastructure.py
   ```
   - Creates S3 bucket: `edna-stream-meraki`
   - Deploys Lambda with schema detection
   - Creates API Gateway endpoint
   - Creates Firehose stream
   - Creates IAM roles

4. **Test Webhook**
   ```bash
   python test_webhook.py
   ```

5. **Configure Meraki Dashboard**
   - Add webhook receiver with API Gateway URL
   - Select alert types to send

## Current Credentials

**Update credentials.yaml with fresh tokens when expired (every 30 min):**

```yaml
production:
  aws_access_key_id: [PASTE_HERE]
  aws_secret_access_key: [PASTE_HERE]
  aws_session_token: [PASTE_HERE]
  account_id: "309820967897"

nonproduction:
  aws_access_key_id: [PASTE_HERE]
  aws_secret_access_key: [PASTE_HERE]
  aws_session_token: [PASTE_HERE]
  account_id: "205372355929"

redshift:
  password: YOUR_PASSWORD

ssh:
  password: YOUR_SSH_PASSWORD
```

## Key Configuration

**Database:** db02  
**Schema:** edna_stream_meraki  
**S3 Bucket:** edna-stream-meraki  
**Cluster:** edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com  
**SSH:** 44.207.39.121 (chris.cestari)

## Alert Types Supported (24+)

- Sensor change detected (74%)
- Power supply went down
- Motion detected
- Geofencing violations
- APs up/down
- Clients up/down/connectivity
- Bluetooth visibility
- Cable errors
- Camera hardware failures
- Cellular up/down
- Client IP conflicts
- Security policy violations
- Temperature critical
- And more...

## Schema Flexibility

The Lambda handles:
- Missing fields (nullable columns)
- Unknown alert types (logs + alerts)
- Processing errors (logs + alerts)
- Schema version detection

All records stored with raw JSON for reprocessing.

## Monitoring

**CloudWatch Logs:**
- `/aws/lambda/meraki-webhook-processor`
- `/aws/kinesisfirehose/meraki-redshift-stream`

**Redshift Queries:**
```sql
-- Recent webhooks
SELECT * FROM db02.edna_stream_meraki.meraki_webhooks 
ORDER BY ingestion_timestamp DESC LIMIT 10;

-- Alert type distribution
SELECT alert_type, COUNT(*) 
FROM db02.edna_stream_meraki.meraki_webhooks 
GROUP BY alert_type ORDER BY COUNT(*) DESC;
```

## Files Location

All files in: `c:\Users\cesta\source\repos\sa-stuff\meraki-webhook-streaming`

**NOT in OneDrive** - Git repo only.

## Troubleshooting

**Credentials expired:**
```bash
# Edit credentials.yaml with fresh tokens
# No script needed - just update the file
```

**Schema issues:**
- Check `schema_samples.json` for payload examples
- Review CloudWatch Logs for unknown schema alerts
- Lambda continues processing with best-effort flattening

**SSH tunnel:**
```bash
ssh -L 5439:edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com:5439 chris.cestari@44.207.39.121
```

## Quick Commands

```bash
cd c:\Users\cesta\source\repos\sa-stuff\meraki-webhook-streaming

# Optional: Copy historical data
python copy_historical_data.py

# Required: Setup schema
python setup_redshift_schema.py

# Required: Deploy infrastructure
python deploy_infrastructure.py

# Required: Test
python test_webhook.py
```

## Success Criteria

- [ ] Redshift schema created in db02
- [ ] Lambda deployed with schema detection
- [ ] API Gateway endpoint created
- [ ] Test webhook successful
- [ ] Data appearing in Redshift
- [ ] CloudWatch Logs showing processing
- [ ] Unknown schemas trigger alerts

---

**Ready to proceed with deployment steps 2-4 above.**
