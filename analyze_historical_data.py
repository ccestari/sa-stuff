#!/usr/bin/env python3
"""
Analyze historical Meraki webhook data to identify schema variations
"""
import json
import boto3
import yaml
from collections import defaultdict, Counter

def analyze_data():
    """Analyze historical webhook data for schema variations"""
    
    print("=" * 60)
    print("Analyzing Historical Meraki Webhook Data")
    print("=" * 60)
    
    # Load credentials
    with open('credentials.yaml') as f:
        creds = yaml.safe_load(f)
    
    nonprod_creds = creds['nonproduction']
    
    # Create S3 client for nonproduction
    session = boto3.Session(
        aws_access_key_id=nonprod_creds['aws_access_key_id'],
        aws_secret_access_key=nonprod_creds['aws_secret_access_key'],
        aws_session_token=nonprod_creds['aws_session_token']
    )
    s3 = session.client('s3')
    
    # Load config
    with open('config.json') as f:
        config = json.load(f)
    
    source_bucket = config['s3']['source_bucket']
    source_prefix = config['s3']['source_prefix']
    
    print(f"\nSource: s3://{source_bucket}/{source_prefix}")
    
    # List files
    print("\n1. Listing files...")
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=source_bucket, Prefix=source_prefix)
    
    files = []
    for page in pages:
        if 'Contents' in page:
            files.extend([obj['Key'] for obj in page['Contents'] if obj['Size'] > 0])
    
    print(f"✅ Found {len(files)} files")
    
    # Analyze schema variations
    print("\n2. Analyzing schema variations...")
    
    field_counts = defaultdict(int)
    alert_types = Counter()
    trigger_types = Counter()
    sample_payloads = {}
    total_records = 0
    
    # Sample files (analyze first 50 for speed)
    sample_size = min(50, len(files))
    
    for i, file_key in enumerate(files[:sample_size]):
        try:
            response = s3.get_object(Bucket=source_bucket, Key=file_key)
            content = response['Body'].read().decode('utf-8')
            
            for line in content.strip().split('\n'):
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Extract payload
                    if 'payload' in data and isinstance(data['payload'], dict):
                        payload = data['payload']
                    else:
                        payload = data
                    
                    # Count fields
                    for key in payload.keys():
                        field_counts[key] += 1
                    
                    # Track alert types
                    alert_type = payload.get('alertType', 'unknown')
                    alert_types[alert_type] += 1
                    
                    # Track trigger types
                    alert_data = payload.get('alertData', {})
                    if alert_data:
                        trigger_data = alert_data.get('triggerData', [])
                        if trigger_data and len(trigger_data) > 0:
                            trigger = trigger_data[0].get('trigger', {})
                            trigger_type = trigger.get('type', 'unknown')
                            trigger_types[trigger_type] += 1
                    
                    # Save sample payloads
                    if alert_type not in sample_payloads:
                        sample_payloads[alert_type] = payload
                    
                    total_records += 1
                    
                except json.JSONDecodeError:
                    continue
            
            if (i + 1) % 10 == 0:
                print(f"   Processed {i + 1}/{sample_size} files, {total_records} records")
        
        except Exception as e:
            print(f"   Error processing {file_key}: {e}")
    
    # Print analysis
    print("\n" + "=" * 60)
    print("Analysis Results")
    print("=" * 60)
    
    print(f"\nTotal records analyzed: {total_records}")
    print(f"Files analyzed: {sample_size}/{len(files)}")
    
    print("\n--- Top-Level Fields ---")
    for field, count in sorted(field_counts.items()):
        percentage = (count / total_records) * 100
        print(f"  {field}: {count} ({percentage:.1f}%)")
    
    print("\n--- Alert Types ---")
    for alert_type, count in alert_types.most_common():
        percentage = (count / total_records) * 100
        print(f"  {alert_type}: {count} ({percentage:.1f}%)")
    
    print("\n--- Trigger Types ---")
    for trigger_type, count in trigger_types.most_common():
        percentage = (count / total_records) * 100
        print(f"  {trigger_type}: {count} ({percentage:.1f}%)")
    
    # Save sample payloads
    print("\n3. Saving sample payloads...")
    with open('schema_samples.json', 'w') as f:
        json.dump(sample_payloads, f, indent=2)
    print("✅ Saved to schema_samples.json")
    
    # Check for schema variations
    print("\n--- Schema Variations Detected ---")
    
    required_fields = ['version', 'organizationId', 'networkId', 'deviceSerial', 'alertType']
    missing_required = []
    
    for field in required_fields:
        if field_counts[field] < total_records:
            missing_count = total_records - field_counts[field]
            missing_required.append((field, missing_count))
    
    if missing_required:
        print("⚠️  Some records missing required fields:")
        for field, count in missing_required:
            print(f"  {field}: {count} records missing")
    else:
        print("✅ All records have required fields")
    
    # Recommendations
    print("\n--- Recommendations ---")
    print("1. Lambda should handle nullable fields for:")
    for field, count in field_counts.items():
        if count < total_records * 0.95:  # Less than 95% presence
            print(f"   - {field}")
    
    print("\n2. Alert types to handle:")
    for alert_type in alert_types.keys():
        print(f"   - {alert_type}")
    
    print("\n3. Trigger types to handle:")
    for trigger_type in trigger_types.keys():
        print(f"   - {trigger_type}")
    
    return {
        'total_records': total_records,
        'field_counts': dict(field_counts),
        'alert_types': dict(alert_types),
        'trigger_types': dict(trigger_types),
        'sample_payloads': sample_payloads
    }

if __name__ == "__main__":
    results = analyze_data()
