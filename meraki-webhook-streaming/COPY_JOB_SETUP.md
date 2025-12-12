# Redshift COPY JOB Setup Guide

## Overview
Switching from Firehose to Redshift COPY JOB for automatic S3 → Redshift loading. This works with VPN-restricted Redshift because Redshift initiates the connection.

## Architecture Change

**Before (Not Working)**:
```
Lambda → Firehose → Redshift (blocked by VPN)
```

**After (Working)**:
```
Lambda → S3 (partitioned) → Redshift COPY JOB (auto-loads)
```

## Step 1: Deploy Updated Lambda

```bash
# Update credentials in credentials.yaml first
cd /Users/chris.cestari/Documents/GitHub/sa-stuff/meraki-webhook-streaming

# Deploy
export AWS_ACCESS_KEY_ID=<your_key>
export AWS_SECRET_ACCESS_KEY=<your_secret>
export AWS_SESSION_TOKEN=<your_token>

zip lambda_deployment.zip lambda_function.py
aws lambda update-function-code \
  --function-name meraki-webhook-processor \
  --zip-file fileb://lambda_deployment.zip
```

## Step 2: Test Lambda Writes to S3

```bash
# Send test webhook
curl -X POST https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{"version":"0.1","alertType":"test","deviceName":"TestDevice"}'

# Check S3 for COPY JOB files
aws s3 ls s3://edna-stream-meraki/copy-job/ --recursive | tail -5
```

You should see files like: `copy-job/2025/12/09/21/request-id.json`

## Step 3: Create COPY JOB in Redshift

Connect to Redshift via SSH tunnel:
```bash
ssh -L 5439:edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com:5439 chris.cestari@44.207.39.121
```

Then run the SQL from `setup_copy_job.sql`:

```sql
CREATE OR REPLACE COPY JOB meraki_webhook_loader
FROM 's3://edna-stream-meraki/copy-job/'
IAM_ROLE 'arn:aws:iam::309820967897:role/MerakiFirehoseRole'
INTO edna_stream_meraki.meraki_webhooks
FORMAT JSON 'auto'
TIMEFORMAT 'auto'
TRUNCATECOLUMNS
BLANKSASNULL
EMPTYASNULL
AUTO ON;
```

## Step 4: Verify COPY JOB is Running

```sql
-- Check COPY JOB status
SELECT 
    job_id,
    job_name,
    data_source,
    destination_table,
    job_state,
    last_run_time,
    next_run_time
FROM sys_copy_job
WHERE job_name = 'meraki_webhook_loader';
```

Expected output:
- `job_state`: RUNNING
- `next_run_time`: Within next few minutes

## Step 5: Monitor Data Loading

```sql
-- Check recent loads
SELECT 
    job_name,
    status,
    start_time,
    end_time,
    rows_loaded,
    error_message
FROM sys_load_history
WHERE job_name = 'meraki_webhook_loader'
ORDER BY start_time DESC
LIMIT 10;

-- Verify new data
SELECT 
    COUNT(*) as count,
    MAX(timestamp) as latest
FROM edna_stream_meraki.meraki_webhooks
WHERE timestamp >= CURRENT_DATE;
```

## How COPY JOB Works

1. **Lambda writes** to `s3://edna-stream-meraki/copy-job/YYYY/MM/DD/HH/`
2. **Redshift monitors** S3 location every few minutes
3. **Auto-loads** new files using COPY command
4. **Tracks** loaded files to avoid duplicates
5. **Retries** on failures

## Benefits vs Firehose

✅ **Works with VPN** - Redshift initiates connection  
✅ **Simpler** - No Firehose to manage  
✅ **Cheaper** - No Firehose cost  
✅ **Visible** - Can see files in S3  
✅ **Debuggable** - Can manually COPY files if needed  

## Troubleshooting

### No data loading?

1. Check COPY JOB status:
```sql
SELECT * FROM sys_copy_job WHERE job_name = 'meraki_webhook_loader';
```

2. Check for errors:
```sql
SELECT * FROM stl_load_errors 
WHERE starttime >= CURRENT_DATE - 1
ORDER BY starttime DESC;
```

3. Check IAM role has S3 permissions:
```bash
aws iam get-role-policy \
  --role-name MerakiFirehoseRole \
  --policy-name MerakiFirehosePolicy
```

### Manual load test

```sql
-- Test loading a specific file
COPY edna_stream_meraki.meraki_webhooks
FROM 's3://edna-stream-meraki/copy-job/2025/12/09/21/'
IAM_ROLE 'arn:aws:iam::309820967897:role/MerakiFirehoseRole'
FORMAT JSON 'auto'
TIMEFORMAT 'auto'
TRUNCATECOLUMNS
BLANKSASNULL
EMPTYASNULL;
```

### Pause/Resume COPY JOB

```sql
-- Pause
ALTER COPY JOB meraki_webhook_loader PAUSE;

-- Resume
ALTER COPY JOB meraki_webhook_loader RESUME;
```

## S3 File Format

Lambda writes newline-delimited JSON:
```json
{"timestamp":"2025-12-09T21:46:12Z","source":"meraki_webhook",...}
```

One record per file, partitioned by date/hour for efficient loading.

## Cleanup Old Files

COPY JOB doesn't delete files. Set up S3 lifecycle policy:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket edna-stream-meraki \
  --lifecycle-configuration file://lifecycle.json
```

lifecycle.json:
```json
{
  "Rules": [{
    "Id": "DeleteOldCopyJobFiles",
    "Status": "Enabled",
    "Prefix": "copy-job/",
    "Expiration": {"Days": 7}
  }]
}
```

## Next Steps

1. Deploy updated Lambda
2. Test webhook → S3 flow
3. Create COPY JOB in Redshift
4. Monitor for 24 hours
5. Set up S3 lifecycle policy
6. (Optional) Delete Firehose stream to save costs
