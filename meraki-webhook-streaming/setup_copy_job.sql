-- Setup Redshift COPY JOB for automatic S3 to Redshift loading
-- Run this via SSH tunnel to Redshift

-- 1. Drop existing COPY JOB if it exists
DROP COPY JOB IF EXISTS meraki_webhook_loader;

-- 2. Create COPY JOB to auto-load from S3
CREATE COPY JOB meraki_webhook_loader
FROM 's3://edna-stream-meraki/copy-job/'
IAM_ROLE 'arn:aws:iam::309820967897:role/MerakiFirehoseRole'
INTO edna_stream_meraki.meraki_webhooks
FORMAT JSON 'auto'
TIMEFORMAT 'auto'
TRUNCATECOLUMNS
BLANKSASNULL
EMPTYASNULL
AUTO ON;

-- 3. Check COPY JOB status
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

-- 4. Check recent COPY JOB runs
SELECT 
    job_id,
    job_name,
    data_source,
    status,
    start_time,
    end_time,
    duration,
    rows_loaded,
    error_message
FROM sys_load_history
WHERE job_name = 'meraki_webhook_loader'
ORDER BY start_time DESC
LIMIT 10;

-- 5. Check for any load errors
SELECT 
    starttime,
    filename,
    line_number,
    colname,
    err_reason
FROM stl_load_errors
WHERE starttime >= CURRENT_DATE - 1
ORDER BY starttime DESC
LIMIT 20;

-- 6. Verify data is loading
SELECT 
    COUNT(*) as total_records,
    MAX(timestamp) as latest_timestamp,
    MIN(timestamp) as earliest_timestamp
FROM edna_stream_meraki.meraki_webhooks
WHERE timestamp >= CURRENT_DATE;

-- 7. To pause COPY JOB (if needed)
-- ALTER COPY JOB meraki_webhook_loader PAUSE;

-- 8. To resume COPY JOB (if needed)
-- ALTER COPY JOB meraki_webhook_loader RESUME;

-- 9. To drop COPY JOB (if needed)
-- DROP COPY JOB meraki_webhook_loader;
