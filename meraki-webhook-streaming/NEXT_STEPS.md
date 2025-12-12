# Next Steps - Complete COPY JOB Setup

## ✅ What's Working Now

1. **Lambda deployed** - Writing to S3 in COPY JOB format
2. **Test successful** - File created at `s3://edna-stream-meraki/copy-job/2025/12/09/22/`
3. **Format verified** - Newline-delimited JSON ready for Redshift

## 🔧 What You Need to Do

### Step 1: Connect to Redshift via SSH Tunnel

```bash
ssh -L 5439:edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com:5439 chris.cestari@44.207.39.121
```

### Step 2: Run the COPY JOB SQL

Connect to Redshift (localhost:5439) and run:

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

### Step 3: Verify COPY JOB is Running

```sql
SELECT 
    job_id,
    job_name,
    job_state,
    last_run_time,
    next_run_time
FROM sys_copy_job
WHERE job_name = 'meraki_webhook_loader';
```

Expected: `job_state = 'RUNNING'`

### Step 4: Check Data is Loading

Wait 2-5 minutes, then:

```sql
-- Check load history
SELECT 
    job_name,
    status,
    start_time,
    rows_loaded,
    error_message
FROM sys_load_history
WHERE job_name = 'meraki_webhook_loader'
ORDER BY start_time DESC
LIMIT 5;

-- Verify new data
SELECT 
    COUNT(*) as new_records,
    MAX(timestamp) as latest
FROM edna_stream_meraki.meraki_webhooks
WHERE timestamp >= CURRENT_DATE;
```

### Step 5: Send Real Webhook from Meraki

Your Meraki Dashboard is already configured to send to:
`https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook`

Real webhooks will now flow automatically!

## 📊 Monitoring

### Check S3 Files
```bash
aws s3 ls s3://edna-stream-meraki/copy-job/ --recursive | tail -10
```

### Check Lambda Logs
```bash
aws logs tail /aws/lambda/meraki-webhook-processor --since 10m
```

### Check Redshift Errors
```sql
SELECT 
    starttime,
    filename,
    err_reason
FROM stl_load_errors
WHERE starttime >= CURRENT_DATE - 1
ORDER BY starttime DESC
LIMIT 10;
```

## 🎯 Success Criteria

- [ ] COPY JOB created in Redshift
- [ ] COPY JOB status = RUNNING
- [ ] Test webhook data appears in Redshift
- [ ] Real Meraki webhooks loading automatically
- [ ] No errors in stl_load_errors

## 📝 Files Reference

- **Lambda Code**: [lambda_function.py](lambda_function.py)
- **SQL Setup**: [setup_copy_job.sql](setup_copy_job.sql)
- **Full Guide**: [COPY_JOB_SETUP.md](COPY_JOB_SETUP.md)

## 🔄 Architecture

```
Meraki Dashboard
    ↓
API Gateway
    ↓
Lambda (meraki-webhook-processor)
    ↓
S3 (copy-job/YYYY/MM/DD/HH/)
    ↓
Redshift COPY JOB (auto-loads every few minutes)
    ↓
edna_stream_meraki.meraki_webhooks
```

## 💡 Benefits

✅ Works with VPN-restricted Redshift  
✅ No Firehose needed (simpler, cheaper)  
✅ Files visible in S3 for debugging  
✅ Near real-time (2-5 min delay)  
✅ Automatic retry on failures  

## ⚠️ Troubleshooting

If COPY JOB doesn't load data:

1. **Check IAM role permissions**:
   - MerakiFirehoseRole needs S3 read access
   - Redshift needs to assume this role

2. **Verify S3 path**:
   - Files must be in `s3://edna-stream-meraki/copy-job/`
   - Check with: `aws s3 ls s3://edna-stream-meraki/copy-job/ --recursive`

3. **Check Redshift cluster**:
   - Must be running (not paused)
   - Check with Redshift console

4. **Manual test**:
```sql
-- Try loading one file manually
COPY edna_stream_meraki.meraki_webhooks
FROM 's3://edna-stream-meraki/copy-job/2025/12/09/22/93e8c819-8116-466a-8e06-58c10a4f8568.json'
IAM_ROLE 'arn:aws:iam::309820967897:role/MerakiFirehoseRole'
FORMAT JSON 'auto'
TIMEFORMAT 'auto'
TRUNCATECOLUMNS
BLANKSASNULL
EMPTYASNULL;
```

## 🎉 Once Complete

You'll have a fully automated pipeline:
- Meraki sends webhooks
- Lambda processes and stores to S3
- Redshift auto-loads every few minutes
- Data available for queries in near real-time!
