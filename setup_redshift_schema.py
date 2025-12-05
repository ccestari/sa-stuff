#!/usr/bin/env python3
"""
Setup Redshift schema for Meraki webhook data
Creates flexible schema to handle varying payload structures
"""
import json
import psycopg2
import os
import yaml
from sshtunnel import SSHTunnelForwarder

def create_schema():
    """Create Redshift schema and table for Meraki webhooks"""
    
    with open('config.json') as f:
        config = json.load(f)
    
    # Get passwords from credentials file
    try:
        with open('credentials.yaml') as f:
            creds = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ credentials.yaml not found in current directory")
        print("Please copy your credentials.yaml file to this directory")
        return False
    
    redshift_password = creds['redshift']['password']
    ssh_password = creds['ssh']['password']
    
    print("Setting up Redshift schema for Meraki webhooks...")
    
    # SSH tunnel configuration
    ssh_host = config['redshift']['ssh_host']
    ssh_user = config['redshift']['ssh_user']
    
    try:
        # Establish SSH tunnel
        print("Establishing SSH tunnel...")
        print(f"Connecting to {ssh_user}@{ssh_host}...")
        print("Note: You must be on VPN to connect to bastion host")
        
        with SSHTunnelForwarder(
            (ssh_host, 22),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(config['redshift']['cluster_endpoint'], config['redshift']['cluster_port']),
            local_bind_address=('localhost', config['redshift']['tunnel_port']),
            set_keepalive=10.0
        ) as tunnel:
            print("✅ SSH tunnel established")
            
            # Connect to Redshift
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
            
            # Create schema
            print(f"\nCreating schema: {schema_name}")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            print(f"✅ Schema created: {schema_name}")
            
            # Create main webhook table with flexible schema
            # Supports 24+ alert types: Sensor, Power, Motion, Geofencing, APs, Clients, etc.
            print("\nCreating meraki_webhooks table...")
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.meraki_webhooks (
                -- Metadata
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                ingestion_timestamp TIMESTAMP DEFAULT GETDATE(),
                timestamp VARCHAR(50),
                source VARCHAR(50),
                lambda_request_id VARCHAR(100),
                environment VARCHAR(50),
                s3_raw_location VARCHAR(500),
                
                -- Base webhook fields
                version VARCHAR(10),
                shared_secret VARCHAR(100),
                sent_at TIMESTAMP,
                organization_id VARCHAR(50),
                organization_name VARCHAR(200),
                organization_url VARCHAR(500),
                network_id VARCHAR(100),
                network_name VARCHAR(200),
                network_url VARCHAR(500),
                network_tags VARCHAR(1000),
                
                -- Device information
                device_serial VARCHAR(50),
                device_mac VARCHAR(50),
                device_name VARCHAR(200),
                device_url VARCHAR(500),
                device_tags VARCHAR(1000),
                device_model VARCHAR(50),
                
                -- Alert information
                alert_id VARCHAR(100),
                alert_type VARCHAR(200),
                alert_type_id VARCHAR(100),
                alert_level VARCHAR(50),
                occurred_at TIMESTAMP,
                
                -- Alert data
                alert_config_id BIGINT,
                alert_config_name VARCHAR(200),
                started_alerting BOOLEAN,
                
                -- Trigger data
                condition_id BIGINT,
                trigger_ts DOUBLE PRECISION,
                trigger_type VARCHAR(50),
                trigger_node_id BIGINT,
                trigger_sensor_value DOUBLE PRECISION,
                
                -- Raw payload for reference
                payload_json VARCHAR(MAX)
            )
            DISTSTYLE AUTO
            SORTKEY (ingestion_timestamp, occurred_at);
            """
            
            cursor.execute(create_table_sql)
            print(f"✅ Table created: {schema_name}.meraki_webhooks")
            
            # Create view for easy querying
            print("\nCreating convenience views...")
            create_view_sql = f"""
            CREATE OR REPLACE VIEW {schema_name}.recent_alerts AS
            SELECT 
                device_name,
                device_model,
                network_name,
                alert_type,
                alert_level,
                trigger_type,
                trigger_sensor_value,
                occurred_at,
                ingestion_timestamp
            FROM {schema_name}.meraki_webhooks
            WHERE occurred_at >= DATEADD(day, -7, GETDATE())
            ORDER BY occurred_at DESC;
            """
            
            cursor.execute(create_view_sql)
            print(f"✅ View created: {schema_name}.recent_alerts")
            
            # Create temperature alerts view
            create_temp_view_sql = f"""
            CREATE OR REPLACE VIEW {schema_name}.temperature_alerts AS
            SELECT 
                device_name,
                network_name,
                trigger_sensor_value as temperature_celsius,
                ROUND((trigger_sensor_value * 9.0 / 5.0) + 32, 2) as temperature_fahrenheit,
                occurred_at,
                alert_config_name,
                started_alerting
            FROM {schema_name}.meraki_webhooks
            WHERE trigger_type = 'temperature'
            ORDER BY occurred_at DESC;
            """
            
            cursor.execute(create_temp_view_sql)
            print(f"✅ View created: {schema_name}.temperature_alerts")
            
            # Grant permissions
            print("\nGranting permissions...")
            cursor.execute(f"GRANT USAGE ON SCHEMA {schema_name} TO PUBLIC")
            cursor.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema_name} TO PUBLIC")
            print("✅ Permissions granted")
            
            cursor.close()
            conn.close()
            
            print("\n" + "=" * 60)
            print("✅ Redshift schema setup complete!")
            print("=" * 60)
            print(f"\nSchema: {schema_name}")
            print(f"Table: {schema_name}.meraki_webhooks")
            print(f"Views: {schema_name}.recent_alerts, {schema_name}.temperature_alerts")
            
            return True
            
    except Exception as e:
        print(f"❌ Error setting up Redshift schema: {e}")
        return False

if __name__ == "__main__":
    create_schema()
