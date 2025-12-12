# Backfill Instructions

## Problem
Records in Redshift have NULL values for most fields because the COPY command isn't properly mapping the JSON fields.

## Solution
The Lambda is correctly extracting all fields to S3. We need to reload the data from S3 with proper field mapping.

## Steps

### 1. Connect to Redshift Query Editor v2
- Go to AWS Console → Redshift → Query Editor v2
- Connect to cluster: edna-prod-dw
- Database: db02

### 2. Run this SQL:

```sql
-- Truncate and reload with proper field mapping
TRUNCATE TABLE edna_stream_meraki.meraki_webhooks;

COPY edna_stream_meraki.meraki_webhooks (
    timestamp, source, lambda_request_id, environment, s3_raw_location,
    version, shared_secret, sent_at,
    organization_id, organization_name, organization_url,
    network_id, network_name, network_url, network_tags,
    device_serial, device_mac, device_name, device_url, device_tags, device_model,
    alert_id, alert_type, alert_type_id, alert_level, occurred_at,
    alert_config_id, alert_config_name, started_alerting,
    condition_id, trigger_ts, trigger_type, trigger_node_id, trigger_sensor_value
)
FROM 's3://edna-stream-meraki/copy-job/'
ACCESS_KEY_ID '<YOUR_ACCESS_KEY>'
SECRET_ACCESS_KEY '<YOUR_SECRET_KEY>'
SESSION_TOKEN '<YOUR_SESSION_TOKEN>'
JSON 'auto'
TIMEFORMAT 'auto'
REGION 'us-east-1'
TRUNCATECOLUMNS
BLANKSASNULL
EMPTYASNULL;
```

### 3. Verify the load:

```sql
SELECT 
    COUNT(*) as total_records,
    COUNT(device_name) as records_with_device_name,
    COUNT(alert_type) as records_with_alert_type,
    COUNT(trigger_sensor_value) as records_with_sensor_value,
    MIN(occurred_at) as earliest,
    MAX(occurred_at) as latest
FROM edna_stream_meraki.meraki_webhooks;
```

### 4. Check sample data:

```sql
SELECT 
    device_name,
    alert_type,
    trigger_type,
    trigger_sensor_value,
    occurred_at
FROM edna_stream_meraki.meraki_webhooks
ORDER BY occurred_at DESC
LIMIT 10;
```

## Expected Results
- All fields should now have values (not NULL)
- device_name, alert_type, trigger_sensor_value should be populated
- Total records should match the number of files in S3

## Note
The Lambda function is already correctly extracting all fields. This is a one-time backfill to fix existing records.
