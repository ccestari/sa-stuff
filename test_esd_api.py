#!/usr/bin/env python3
"""Test ESD Period Attendance API"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sa-utils/aws-utils'))

import requests
import json
from credential_manager import CredentialManager

BASE_URL = "https://guru-ren.eschooldata.com:443/api"

def get_esd_credentials():
    cred_mgr = CredentialManager('credentials.yaml')
    cred_mgr.ensure_valid_credentials()
    session = cred_mgr.get_session()
    client = session.client('secretsmanager')
    secret = client.get_secret_value(SecretId="prod/edna/esd_api_token")
    return json.loads(secret['SecretString'])

def get_esd_token():
    creds = get_esd_credentials()
    response = requests.post(creds['ESD_URL'], data={
        'grant_type': 'client_credentials',
        'client_id': creds['ESD_CLIENT_ID'],
        'client_secret': creds['ESD_SECRET_KEY']
    })
    response.raise_for_status()
    return response.json()['access_token']

print("🔑 Getting token...")
token = get_esd_token()
headers = {"Authorization": f"Bearer {token}"}
print("✅ Token obtained\n")

# Test with school 12549 (from your example)
school_id = 12549
url = f"{BASE_URL}/v1/periodAttendance"
params = {"schoolId": school_id}

print(f"📡 Testing: {url}")
print(f"   Params: {params}\n")

response = requests.get(url, headers=headers, params=params)
print(f"Status: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")
