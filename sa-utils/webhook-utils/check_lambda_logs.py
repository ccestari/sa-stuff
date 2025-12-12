#!/usr/bin/env python3
"""Check Lambda CloudWatch logs - works with any webhook project"""
import boto3
import json
import yaml
import sys
from datetime import datetime, timedelta

def check_lambda_logs(config_path='config.json', credentials_path='credentials.yaml', hours=1):
    with open(config_path) as f:
        config = json.load(f)

    with open(credentials_path) as f:
        creds = yaml.safe_load(f)

    prod_creds = creds['production']
    session = boto3.Session(
        aws_access_key_id=prod_creds['aws_access_key_id'],
        aws_secret_access_key=prod_creds['aws_secret_access_key'],
        aws_session_token=prod_creds['aws_session_token']
    )

    logs = session.client('logs')
    log_group = f"/aws/lambda/{config['lambda']['function_name']}"

    print(f"Checking logs for: {log_group}")
    print("=" * 60)

    try:
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
        
        response = logs.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            limit=50
        )
        
        if response['events']:
            print(f"\nFound {len(response['events'])} log events in last {hours} hour(s):\n")
            for event in response['events']:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"[{timestamp}] {event['message']}")
        else:
            print(f"\n❌ No log events found in last {hours} hour(s)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    creds = sys.argv[2] if len(sys.argv) > 2 else 'credentials.yaml'
    hours = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    check_lambda_logs(config, creds, hours)
