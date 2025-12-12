#!/usr/bin/env python3
"""Test ESD Period Attendance API - Simple version"""
import requests
import json

BASE_URL = "https://guru-ren.eschooldata.com:443/api"

# You need to provide a valid ESD Bearer token here
# Get it from AWS Secrets Manager or generate a new one
ESD_TOKEN = "PASTE_TOKEN_HERE"

headers = {"Authorization": f"Bearer {ESD_TOKEN}"}

# Test with school 12549 (from your example)
school_id = 12549
url = f"{BASE_URL}/v1/periodAttendance"
params = {"schoolId": school_id}

print(f"📡 Testing: {url}")
print(f"   Params: {params}\n")

response = requests.get(url, headers=headers, params=params)
print(f"Status: {response.status_code}")
print(f"\nResponse structure:")
data = response.json()
print(f"Type: {type(data)}")
if isinstance(data, dict):
    print(f"Keys: {list(data.keys())}")
    if 'periodAttendance' in data:
        print(f"periodAttendance count: {len(data.get('periodAttendance', []))}")
    if 'pagingInfo' in data:
        print(f"Paging info: {data['pagingInfo']}")
elif isinstance(data, list):
    print(f"List length: {len(data)}")
    if len(data) > 0:
        print(f"First item keys: {list(data[0].keys())}")

print(f"\nFull response:\n{json.dumps(data, indent=2)[:1000]}")
