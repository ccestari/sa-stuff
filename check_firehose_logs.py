#!/usr/bin/env python3
"""Check Firehose CloudWatch logs"""
import boto3
import json
import yaml
from datetime import datetime, timedelta

with open('config.json') as f:
    config = json.load(f)

with open('credentials.yaml') as f:
    creds = yaml.safe_load(f)

prod_creds = creds['production']
session = boto3.Session(
    aws_access_key_id=prod_creds['aws_access_key_id'],
    aws_secret_access_key=prod_creds['aws_secret_access_key'],
    aws_session_token=prod_creds['aws_session_token']
)

logs = session.client('logs')
log_group = f"/aws/kinesisfirehose/{config['firehose']['stream_name']}"

print(f"Checking Firehose logs: {log_group}")
print("=" * 60)

try:
    start_time = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
    
    response = logs.filter_log_events(
        logGroupName=log_group,
        startTime=start_time,
        limit=100
    )
    
    if response['events']:
        print(f"\nFound {len(response['events'])} log events:\n")
        for event in response['events']:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            print(f"[{timestamp}] {event['message']}")
    else:
        print("\n❌ No Firehose log events found")
        
except Exception as e:
    print(f"❌ Error: {e}")
