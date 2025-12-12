#!/usr/bin/env python3
"""Load S3 data to Redshift via COPY command"""
import boto3
import yaml
import json
import psycopg2
from sshtunnel import SSHTunnelForwarder

with open('config.json') as f:
    config = json.load(f)

with open('credentials.yaml') as f:
    creds = yaml.safe_load(f)

prod_creds = creds['production']
redshift_password = creds['redshift']['password']
ssh_password = creds['ssh']['password']

print("⚠️  This requires VPN connection to SSH bastion host")
print("Connecting via SSH tunnel...")

try:
    with SSHTunnelForwarder(
        (config['redshift']['ssh_host'], 22),
        ssh_username=config['redshift']['ssh_user'],
        ssh_password=ssh_password,
        remote_bind_address=(config['redshift']['cluster_endpoint'], config['redshift']['cluster_port']),
        local_bind_address=('localhost', config['redshift']['tunnel_port']),
        set_keepalive=10.0
    ) as tunnel:
        print("✅ SSH tunnel established")
        
        conn = psycopg2.connect(
            host='localhost',
            port=config['redshift']['tunnel_port'],
            database=config['redshift']['database'],
            user=config['redshift']['admin_user'],
            password=redshift_password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # COPY from S3
        copy_sql = f"""
        COPY {config['redshift']['target_schema']}.meraki_webhooks
        FROM 's3://{config['s3']['raw_bucket']}/firehose-backup/'
        IAM_ROLE '{config['redshift']['cluster_arn']}'
        FORMAT AS JSON 'auto'
        GZIP
        TIMEFORMAT 'auto';
        """
        
        print("\nLoading data from S3 to Redshift...")
        print(f"Source: s3://{config['s3']['raw_bucket']}/firehose-backup/")
        print(f"Target: {config['redshift']['target_schema']}.meraki_webhooks")
        
        cursor.execute(copy_sql)
        
        cursor.execute(f"SELECT COUNT(*) FROM {config['redshift']['target_schema']}.meraki_webhooks")
        count = cursor.fetchone()[0]
        
        print(f"\n✅ Load complete!")
        print(f"Total rows in table: {count}")
        
        cursor.close()
        conn.close()
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nMake sure you're connected to VPN!")
