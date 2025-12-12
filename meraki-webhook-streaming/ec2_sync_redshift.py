#!/usr/bin/env python3
"""
Run on EC2 bastion - syncs S3 to Redshift every 5 minutes
No SSH tunnel needed since EC2 is in VPN
"""
import psycopg2
import boto3
import time
from datetime import datetime

# Redshift connection (direct - no SSH tunnel)
REDSHIFT_HOST = 'edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com'
REDSHIFT_PORT = 5439
REDSHIFT_DB = 'db02'
REDSHIFT_USER = 'ccestari'
REDSHIFT_PASSWORD = 'Cc@succ123!'

# AWS credentials (use IAM role on EC2 instead)
S3_BUCKET = 'edna-stream-meraki'
S3_PREFIX = 'copy-job/'

def sync_to_redshift():
    print(f"[{datetime.now()}] Starting sync...")
    
    try:
        # Get AWS credentials from EC2 instance role
        session = boto3.Session()
        credentials = session.get_credentials()
        
        # Connect to Redshift
        conn = psycopg2.connect(
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT,
            database=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Run COPY command
        copy_sql = f"""
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
        FROM 's3://{S3_BUCKET}/{S3_PREFIX}'
        ACCESS_KEY_ID '{credentials.access_key}'
        SECRET_ACCESS_KEY '{credentials.secret_key}'
        SESSION_TOKEN '{credentials.token}'
        JSON 'auto'
        TIMEFORMAT 'auto'
        REGION 'us-east-1'
        TRUNCATECOLUMNS
        BLANKSASNULL
        EMPTYASNULL;
        """
        
        cursor.execute(copy_sql)
        
        cursor.execute("SELECT COUNT(*) FROM edna_stream_meraki.meraki_webhooks")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"[{datetime.now()}] ✅ Sync complete. Total records: {count}")
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")

if __name__ == "__main__":
    print("Meraki S3 → Redshift Sync (Every 5 minutes)")
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            sync_to_redshift()
            time.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            print("\nStopping...")
            break
