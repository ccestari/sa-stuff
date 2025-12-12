#!/usr/bin/env python3
"""Check what date range is actually available in the API"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sa-utils/aws-utils'))

import requests
import json
from credential_manager import CredentialManager

BASE_URL = "https://guru-ren.eschooldata.com:443/api"

def get_token():
    cred_mgr = CredentialManager('credentials.yaml')
    cred_mgr.ensure_valid_credentials()
    session = cred_mgr.get_session()
    client = session.client('secretsmanager')
    secret = client.get_secret_value(SecretId="prod/edna/esd_api_token")
    creds = json.loads(secret['SecretString'])
    response = requests.post(creds['ESD_URL'], data={
        'grant_type': 'client_credentials',
        'client_id': creds['ESD_CLIENT_ID'],
        'client_secret': creds['ESD_SECRET_KEY']
    })
    return response.json()['access_token']

token = get_token()
headers = {"Authorization": f"Bearer {token}"}

# Test school 12549 with different date ranges
school_id = 12549

print("Testing different date ranges for school 12549:\n")

# Test 1: No date params
print("1. No date parameters:")
response = requests.get(f"{BASE_URL}/v1/periodAttendance", 
    headers=headers, params={"schoolId": school_id, "pageSize": 10})
data = response.json()
dates = [r['date'] for r in data.get('periodAttendanceList', [])]
print(f"   Dates: {sorted(set(dates))}")
print(f"   Total available: {data.get('pagingInfo', {}).get('totalCount', 0)}\n")

# Test 2: Last 30 days
print("2. Last 30 days (2024-11-10 to 2025-12-10):")
response = requests.get(f"{BASE_URL}/v1/periodAttendance",
    headers=headers, params={"schoolId": school_id, "startDate": "2024-11-10", "endDate": "2025-12-10", "pageSize": 10})
data = response.json()
dates = [r['date'] for r in data.get('periodAttendanceList', [])]
print(f"   Dates: {sorted(set(dates))}")
print(f"   Total: {data.get('pagingInfo', {}).get('totalCount', 0)}\n")

# Test 3: Last year
print("3. Last year (2024-01-01 to 2025-12-10):")
response = requests.get(f"{BASE_URL}/v1/periodAttendance",
    headers=headers, params={"schoolId": school_id, "startDate": "2024-01-01", "endDate": "2025-12-10", "pageSize": 10})
data = response.json()
dates = [r['date'] for r in data.get('periodAttendanceList', [])]
print(f"   Dates: {sorted(set(dates))}")
print(f"   Total: {data.get('pagingInfo', {}).get('totalCount', 0)}\n")
