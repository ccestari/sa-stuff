-- Run this in Redshift Query Editor v2 to backfill fields from S3
-- This will reload all data from S3 with proper field extraction

-- First, truncate the table
TRUNCATE TABLE edna_stream_meraki.meraki_webhooks;

-- Load from S3 with all fields properly mapped
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

-- Verify the load
SELECT 
    COUNT(*) as total_records,
    COUNT(device_name) as records_with_device_name,
    COUNT(alert_type) as records_with_alert_type,
    MIN(occurred_at) as earliest,
    MAX(occurred_at) as latest
FROM edna_stream_meraki.meraki_webhooks;
