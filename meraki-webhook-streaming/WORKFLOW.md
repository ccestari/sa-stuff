# Deployment Workflow

## Overview

This workflow splits tasks between two computers:
- **Windows PC** (this computer): Main development, testing, monitoring
- **Mac** (work computer): VPN-only tasks (Redshift schema setup)

## Phase 1: Prepare on Windows PC ✅ COMPLETE

- [x] Analyze historical data (3,336 files)
- [x] Create configuration files
- [x] Develop Lambda function with schema detection
- [x] Create deployment scripts
- [x] Clean git history
- [x] Push to remote repository

## Phase 2: VPN Tasks on Mac (One-Time Setup)

### On Mac:

1. **Clone repository**
   ```bash
   git clone YOUR_REPO_URL
   cd meraki-webhook-streaming
   ```

2. **Install dependencies**
   ```bash
   pip install boto3 psycopg2-binary paramiko==2.12.0 sshtunnel==0.4.0 pyyaml
   ```

3. **Create credentials.yaml**
   ```bash
   cp credentials.yaml.template credentials.yaml
   nano credentials.yaml  # Add fresh AWS credentials
   ```

4. **Connect to VPN** ⚠️ REQUIRED

5. **Setup Redshift schema**
   ```bash
   python setup_redshift_schema.py
   ```
   
   This creates:
   - Schema: edna_stream_meraki
   - Table: meraki_webhooks
   - Views: recent_alerts, temperature_alerts

6. **Commit and push** (if schema script made any changes)
   ```bash
   git add .
   git commit -m "Redshift schema created"
   git push
   ```

## Phase 3: Return to Windows PC

### On Windows:

1. **Pull latest changes**
   ```bash
   cd c:\Users\cesta\source\repos\sa-stuff\meraki-webhook-streaming
   git pull
   ```

2. **Update credentials.yaml** (if needed - credentials expire every 30 min)

3. **Deploy infrastructure**
   ```bash
   python deploy_infrastructure.py
   ```
   
   This creates:
   - S3 bucket: edna-stream-meraki
   - Lambda: meraki-webhook-processor
   - API Gateway: meraki-webhook-api
   - Firehose: meraki-redshift-stream
   - IAM roles
   
   **Save the API Gateway URL!**

4. **Test webhook**
   ```bash
   python test_webhook.py
   ```

5. **Configure Meraki Dashboard**
   - Use API Gateway URL as webhook endpoint
   - Select alert types to receive

6. **Monitor**
   ```bash
   # Lambda logs
   aws logs tail /aws/lambda/meraki-webhook-processor --follow
   
   # Check Redshift (requires VPN - do on Mac if needed)
   # SELECT * FROM edna_stream_meraki.recent_alerts LIMIT 10;
   ```

7. **Optional: Load historical data**
   ```bash
   python copy_historical_data.py
   ```

## Phase 4: Ongoing Operations (Windows PC)

### Daily Tasks
- Monitor CloudWatch logs
- Check webhook delivery
- Query Redshift for data validation (via Mac if VPN needed)

### When Credentials Expire (every 30 min)
1. Get fresh credentials from AWS SSO
2. Update credentials.yaml
3. Continue working

### When Schema Changes Needed
1. Update setup_redshift_schema.py on Windows
2. Commit and push
3. Pull on Mac
4. Connect to VPN
5. Run: `python setup_redshift_schema.py`
6. Return to Windows

## Quick Reference

### Windows PC (Main Development)
- ✅ Code development
- ✅ AWS infrastructure deployment
- ✅ Testing webhooks
- ✅ Monitoring CloudWatch
- ✅ S3 operations
- ✅ Historical data analysis
- ❌ Redshift schema changes (requires VPN)

### Mac (VPN Tasks Only)
- ✅ Redshift schema setup/changes
- ✅ Direct Redshift queries
- ❌ Everything else (use Windows)

## Communication Pattern

When working across computers:

1. **Windows → Mac**: Commit and push changes
2. **Mac**: Pull, run VPN tasks, commit results
3. **Mac → Windows**: Push changes
4. **Windows**: Pull and continue

## Files to Sync

Always commit/push:
- Python scripts
- config.json
- Documentation

Never commit:
- credentials.yaml (gitignored)
- deployment_info.json (gitignored)
- schema_samples.json (gitignored)

## Troubleshooting

### Can't connect to Redshift from Windows
- Expected - requires VPN
- Use Mac for Redshift tasks

### Credentials expired
- Update credentials.yaml with fresh credentials from AWS SSO
- Happens every 30 minutes

### Need to update schema
- Edit setup_redshift_schema.py on Windows
- Push to git
- Pull on Mac, connect VPN, run script
- Return to Windows

## Success Criteria

- [x] Historical data analyzed
- [x] Code developed and tested
- [x] Git repository clean (no credentials)
- [ ] Redshift schema created (Mac + VPN)
- [ ] Infrastructure deployed (Windows)
- [ ] Webhook tested (Windows)
- [ ] Meraki Dashboard configured (Windows)
- [ ] Data flowing to Redshift (verify on Mac + VPN)
