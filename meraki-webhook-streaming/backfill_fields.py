#!/usr/bin/env python3
"""
Backfill fields from payload_json for existing records with NULL values
"""
import psycopg2
import json
import yaml
from sshtunnel import SSHTunnelForwarder

with open('config.json') as f:
    config = json.load(f)

with open('credentials.yaml') as f:
    creds = yaml.safe_load(f)

print("Connecting to Redshift via SSH tunnel...")

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
    conn.autocommit = False
    cursor = conn.cursor()
    
    # Get records with NULL fields but non-NULL payload_json
    cursor.execute("""
        SELECT id, payload_json 
        FROM edna_stream_meraki.meraki_webhooks 
        WHERE payload_json IS NOT NULL 
        AND (device_name IS NULL OR alert_type IS NULL)
        LIMIT 1000
    """)
    
    records = cursor.fetchall()
    print(f"Found {len(records)} records to update")
    
    updated = 0
    for record_id, payload_json in records:
        try:
            payload = json.loads(payload_json)
            
            # Extract fields
            alert_data = payload.get('alertData', {})
            trigger_data = alert_data.get('triggerData', [])
            trigger = trigger_data[0].get('trigger', {}) if trigger_data else {}
            
            cursor.execute("""
                UPDATE edna_stream_meraki.meraki_webhooks
                SET 
                    version = %s,
                    shared_secret = %s,
                    sent_at = %s,
                    organization_id = %s,
                    organization_name = %s,
                    organization_url = %s,
                    network_id = %s,
                    network_name = %s,
                    network_url = %s,
                    network_tags = %s,
                    device_serial = %s,
                    device_mac = %s,
                    device_name = %s,
                    device_url = %s,
                    device_tags = %s,
                    device_model = %s,
                    alert_id = %s,
                    alert_type = %s,
                    alert_type_id = %s,
                    alert_level = %s,
                    occurred_at = %s,
                    alert_config_id = %s,
                    alert_config_name = %s,
                    started_alerting = %s,
                    condition_id = %s,
                    trigger_ts = %s,
                    trigger_type = %s,
                    trigger_node_id = %s,
                    trigger_sensor_value = %s
                WHERE id = %s
            """, (
                payload.get('version'),
                payload.get('sharedSecret'),
                payload.get('sentAt'),
                payload.get('organizationId'),
                payload.get('organizationName'),
                payload.get('organizationUrl'),
                payload.get('networkId'),
                payload.get('networkName'),
                payload.get('networkUrl'),
                json.dumps(payload.get('networkTags', [])),
                payload.get('deviceSerial'),
                payload.get('deviceMac'),
                payload.get('deviceName'),
                payload.get('deviceUrl'),
                json.dumps(payload.get('deviceTags', [])),
                payload.get('deviceModel'),
                payload.get('alertId'),
                payload.get('alertType'),
                payload.get('alertTypeId'),
                payload.get('alertLevel'),
                payload.get('occurredAt'),
                alert_data.get('alertConfigId'),
                alert_data.get('alertConfigName'),
                alert_data.get('startedAlerting'),
                trigger_data[0].get('conditionId') if trigger_data else None,
                trigger.get('ts'),
                trigger.get('type'),
                trigger.get('nodeId'),
                trigger.get('sensorValue'),
                record_id
            ))
            
            updated += 1
            if updated % 100 == 0:
                print(f"Updated {updated} records...")
                conn.commit()
                
        except Exception as e:
            print(f"Error updating record {record_id}: {e}")
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n✅ Updated {updated} records")
