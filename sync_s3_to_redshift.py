#!/usr/bin/env python3
"""
Sync S3 webhooks to Redshift every 5 minutes
Runs COPY command to load new data from S3
"""
import time
import psycopg2
import json
import yaml
from datetime import datetime
from sshtunnel import SSHTunnelForwarder

def sync_to_redshift():
    with open('config.json') as f:
        config = json.load(f)
    
    with open('credentials.yaml') as f:
        creds = yaml.safe_load(f)
    
    print(f"[{datetime.now()}] Starting sync...")
    
    try:
        with SSHTunnelForwarder(
            (config['redshift']['ssh_host'], 22),
            ssh_username=config['redshift']['ssh_user'],
            ssh_password=creds['ssh']['password'],
            remote_bind_address=(config['redshift']['cluster_endpoint'], config['redshift']['cluster_port']),
            local_bind_address=('localhost', config['redshift']['tunnel_port'])
        ) as tunnel:
            
            conn = psycopg2.connect(
                host='localhost',
                port=config['redshift']['tunnel_port'],
                database=config['redshift']['database'],
                user=config['redshift']['admin_user'],
                password=creds['redshift']['password']
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            schema = config['redshift']['target_schema']
            
            # Get AWS credentials
            aws_creds = creds['production']
            
            # Run COPY command
            copy_sql = f"""
            COPY {schema}.meraki_webhooks (
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
            FROM 's3://{config['s3']['backup_bucket']}/raw/'
            ACCESS_KEY_ID '{aws_creds['aws_access_key_id']}'
            SECRET_ACCESS_KEY '{aws_creds['aws_secret_access_key']}'
            SESSION_TOKEN '{aws_creds['aws_session_token']}'
            JSON 'auto'
            TIMEFORMAT 'auto'
            REGION '{config['aws']['region']}'
            TRUNCATECOLUMNS
            BLANKSASNULL
            EMPTYASNULL;
            """
            
            cursor.execute(copy_sql)
            
            # Get count
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.meraki_webhooks")
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"[{datetime.now()}] ✅ Sync complete. Total records: {count}")
            
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Meraki S3 → Redshift Sync (Every 5 minutes)")
    print("=" * 60)
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            sync_to_redshift()
            time.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            print("\n\nStopping sync...")
            break
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Unexpected error: {e}")
            time.sleep(300)
