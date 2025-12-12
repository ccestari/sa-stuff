#!/usr/bin/env python3
"""Quick credential updater for continuous_sync.sh"""
import yaml
import sys

print("\n🔑 Update AWS Credentials")
print("=" * 60)

# Get new credentials
access_key = input("aws_access_key_id: ").strip()
secret_key = input("aws_secret_access_key: ").strip()
session_token = input("aws_session_token: ").strip()

if not access_key or not secret_key or not session_token:
    print("❌ All fields required")
    sys.exit(1)

# Update credentials.yaml
with open('credentials.yaml', 'r') as f:
    creds = yaml.safe_load(f)

creds['production']['aws_access_key_id'] = access_key
creds['production']['aws_secret_access_key'] = secret_key
creds['production']['aws_session_token'] = session_token

with open('credentials.yaml', 'w') as f:
    yaml.dump(creds, f)

print("✅ Credentials updated in credentials.yaml")
