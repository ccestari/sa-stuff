#!/usr/bin/env python3
"""
Load historical Meraki webhook data from S3 to Redshift
Source: s3://edna-dev-meraki-webhooks/webhook-data/
"""
import json
import boto3
import psycopg2
import os
from datetime import datetime
from sshtunnel import SSHTunnelForwarder
from setup_credentials import CredentialManager

def load_historical_data():
    """Load historical webhook data from S3 to Redshift"""
    
    print("=" * 60)
    print("Loading Historical Meraki Webhook Data")
    print("=" * 60)
    
    # Load config
    with open('config.json') as f:
        config = json.load(f)
    
    # Check credentials
    cred_manager = CredentialManager()
    if not cred_manager.load_credentials() or not cred_manager.are_credentials_valid():
        print("❌ AWS credentials invalid. Run: python setup_credentials.py")
        return False
    
    session = cred_manager.get_boto3_session()
    s3 = session.client('s3')
    
    # Get passwords
    redshift_password = os.environ.get('REDSHIFT_PASSWORD')
    ssh_password = os.environ.get('SSH_PASSWORD')
    
    if not redshift_password:
        redshift_password = input("Enter Redshift password: ")
    if not ssh_password:
        ssh_password = input("Enter SSH password: ")
    
    # List files in source bucket
    print("\n1. Listing files in source bucket...")
    source_bucket = config['s3']['source_bucket']
    source_prefix = config['s3']['source_prefix']
    
    try:
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=source_bucket, Prefix=source_prefix)
        
        files = []
        for page in pages:
            if 'Contents' in page:
                files.extend([obj['Key'] for obj in page['Contents'] if obj['Size'] > 0])
        
        print(f"✅ Found {len(files)} files")
        
        if len(files) == 0:
            print("❌ No files found in source bucket")
            return False
        
        # Show sample
        print(f"\nSample files:")
        for f in files[:5]:
            print(f"   - {f}")
        if len(files) > 5:
            print(f"   ... and {len(files) - 5} more")
        
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return False
    
    # Ask for confirmation
    print(f"\nThis will load {len(files)} files into Redshift.")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled.")
        return False
    
    # Connect to Redshift
    print("\n2. Connecting to Redshift...")
    ssh_host = '44.207.39.121'
    ssh_user = 'chris.cestari'
    
    try:
        with SSHTunnelForwarder(
            (ssh_host, 22),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(config['redshift']['cluster_endpoint'], config['redshift']['cluster_port']),
            local_bind_address=('localhost', config['redshift']['tunnel_port'])
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
            
            schema_name = config['redshift']['target_schema']
            
            # Process files
            print(f"\n3. Processing {len(files)} files...")
            
            processed = 0
            errors = 0
            records_inserted = 0
            
            for i, file_key in enumerate(files):
                try:
                    # Download file
                    response = s3.get_object(Bucket=source_bucket, Key=file_key)
                    content = response['Body'].read().decode('utf-8')
                    
                    # Parse JSON lines
                    lines = content.strip().split('\n')
                    
                    for line in lines:
                        if not line.strip():
                            continue
                        
                        try:
                            webhook_data = json.loads(line)
                            
                            # Extract payload if wrapped
                            if 'payload' in webhook_data and isinstance(webhook_data['payload'], dict):
                                payload = webhook_data['payload']
                            else:
                                payload = webhook_data
                            
                            # Flatten payload
                            flattened = flatten_payload(payload)
                            
                            # Insert into Redshift
                            insert_record(cursor, schema_name, flattened, payload)
                            records_inserted += 1
                            
                        except json.JSONDecodeError:
                            errors += 1
                            continue
                    
                    processed += 1
                    
                    if (i + 1) % 10 == 0:
                        print(f"   Processed {i + 1}/{len(files)} files, {records_inserted} records inserted")
                    
                except Exception as e:
                    print(f"   Error processing {file_key}: {e}")
                    errors += 1
            
            cursor.close()
            conn.close()
            
            print("\n" + "=" * 60)
            print("✅ Historical Data Load Complete")
            print("=" * 60)
            print(f"Files processed: {processed}/{len(files)}")
            print(f"Records inserted: {records_inserted}")
            print(f"Errors: {errors}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def flatten_payload(payload):
    """Flatten Meraki payload to match Redshift schema"""
    flattened = {
        'version': payload.get('version'),
        'shared_secret': payload.get('sharedSecret'),
        'sent_at': payload.get('sentAt'),
        'organization_id': payload.get('organizationId'),
        'organization_name': payload.get('organizationName'),
        'organization_url': payload.get('organizationUrl'),
        'network_id': payload.get('networkId'),
        'network_name': payload.get('networkName'),
        'network_url': payload.get('networkUrl'),
        'network_tags': json.dumps(payload.get('networkTags', [])),
        'device_serial': payload.get('deviceSerial'),
        'device_mac': payload.get('deviceMac'),
        'device_name': payload.get('deviceName'),
        'device_url': payload.get('deviceUrl'),
        'device_tags': json.dumps(payload.get('deviceTags', [])),
        'device_model': payload.get('deviceModel'),
        'alert_id': payload.get('alertId'),
        'alert_type': payload.get('alertType'),
        'alert_type_id': payload.get('alertTypeId'),
        'alert_level': payload.get('alertLevel'),
        'occurred_at': payload.get('occurredAt')
    }
    
    # Alert data
    alert_data = payload.get('alertData', {})
    if alert_data:
        flattened['alert_config_id'] = alert_data.get('alertConfigId')
        flattened['alert_config_name'] = alert_data.get('alertConfigName')
        flattened['started_alerting'] = alert_data.get('startedAlerting')
        
        # Trigger data
        trigger_data = alert_data.get('triggerData', [])
        if trigger_data and len(trigger_data) > 0:
            first_trigger = trigger_data[0]
            flattened['condition_id'] = first_trigger.get('conditionId')
            
            trigger = first_trigger.get('trigger', {})
            flattened['trigger_ts'] = trigger.get('ts')
            flattened['trigger_type'] = trigger.get('type')
            flattened['trigger_node_id'] = trigger.get('nodeId')
            flattened['trigger_sensor_value'] = trigger.get('sensorValue')
    
    return flattened

def insert_record(cursor, schema_name, flattened, raw_payload):
    """Insert record into Redshift"""
    
    insert_sql = f"""
    INSERT INTO {schema_name}.meraki_webhooks (
        timestamp, source, environment,
        version, shared_secret, sent_at,
        organization_id, organization_name, organization_url,
        network_id, network_name, network_url, network_tags,
        device_serial, device_mac, device_name, device_url, device_tags, device_model,
        alert_id, alert_type, alert_type_id, alert_level, occurred_at,
        alert_config_id, alert_config_name, started_alerting,
        condition_id, trigger_ts, trigger_type, trigger_node_id, trigger_sensor_value,
        payload_json
    ) VALUES (
        %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s
    )
    """
    
    cursor.execute(insert_sql, (
        datetime.utcnow().isoformat() + 'Z',
        'meraki_webhook_historical',
        'production',
        flattened.get('version'),
        flattened.get('shared_secret'),
        flattened.get('sent_at'),
        flattened.get('organization_id'),
        flattened.get('organization_name'),
        flattened.get('organization_url'),
        flattened.get('network_id'),
        flattened.get('network_name'),
        flattened.get('network_url'),
        flattened.get('network_tags'),
        flattened.get('device_serial'),
        flattened.get('device_mac'),
        flattened.get('device_name'),
        flattened.get('device_url'),
        flattened.get('device_tags'),
        flattened.get('device_model'),
        flattened.get('alert_id'),
        flattened.get('alert_type'),
        flattened.get('alert_type_id'),
        flattened.get('alert_level'),
        flattened.get('occurred_at'),
        flattened.get('alert_config_id'),
        flattened.get('alert_config_name'),
        flattened.get('started_alerting'),
        flattened.get('condition_id'),
        flattened.get('trigger_ts'),
        flattened.get('trigger_type'),
        flattened.get('trigger_node_id'),
        flattened.get('trigger_sensor_value'),
        json.dumps(raw_payload)
    ))

if __name__ == "__main__":
    load_historical_data()
