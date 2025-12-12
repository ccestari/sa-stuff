#!/usr/bin/env python3
"""
Explore ESD API parameters and response structure
"""
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
    payload = {
        'grant_type': 'client_credentials',
        'client_id': creds['ESD_CLIENT_ID'],
        'client_secret': creds['ESD_SECRET_KEY']
    }
    response = requests.post(creds['ESD_URL'], data=payload)
    response.raise_for_status()
    return response.json()['access_token']

def main():
    print("🔑 Getting OAuth token...")
    token = get_esd_token()
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Token obtained\n")
    
    school_id = 12563
    
    # Test 1: Check response structure with pagination info
    print("📋 Test 1: Full response structure")
    print("-" * 60)
    response = requests.get(
        f"{BASE_URL}/v1/schools/{school_id}/periodAttendance",
        headers=headers,
        params={"pageSize": 5}
    )
    data = response.json()
    
    if isinstance(data, dict):
        print(f"Response keys: {list(data.keys())}")
        
        if 'pagingInfo' in data:
            print(f"\nPaging Info:")
            for key, value in data['pagingInfo'].items():
                print(f"  {key}: {value}")
        
        records = data.get('periodAttendance', [])
    else:
        print("Response is a list (no pagination info)")
        records = data
    
    if len(records) > 0:
        print(f"\nFirst record structure:")
        first_record = records[0]
        for key in sorted(first_record.keys()):
            value = first_record[key]
            if isinstance(value, dict):
                print(f"  {key}: {list(value.keys())}")
            else:
                print(f"  {key}: {value}")
    
    # Test 2: Check if there's a different endpoint for historical data
    print("\n\n📋 Test 2: Check for date-specific fields")
    print("-" * 60)
    sample_records = records[:3]
    for i, record in enumerate(sample_records, 1):
        print(f"\nRecord {i}:")
        print(f"  ID: {record.get('id')}")
        print(f"  Date: {record.get('date')}")
        print(f"  Created: {record.get('createdOn')}")
        print(f"  Modified: {record.get('modifiedOn')}")
    
    # Test 3: Try different parameter combinations
    print("\n\n📋 Test 3: Testing parameter combinations")
    print("-" * 60)
    
    param_tests = [
        {"pageSize": 10},
        {"pageSize": 10, "date": "2025-12-08"},
        {"pageSize": 10, "fromDate": "2025-12-01", "toDate": "2025-12-09"},
        {"pageSize": 10, "startDate": "2025-12-01"},
        {"pageSize": 10, "endDate": "2025-12-09"},
        {"pageSize": 10, "modifiedAfter": "2025-12-01"},
    ]
    
    for params in param_tests:
        try:
            response = requests.get(
                f"{BASE_URL}/v1/schools/{school_id}/periodAttendance",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                records = data.get('periodAttendance', [])
                dates = set(r.get('date') for r in records[:10] if 'date' in r)
                print(f"  {str(params):60s} → {len(records):4d} records, dates: {dates}")
            else:
                print(f"  {str(params):60s} → Error {response.status_code}")
        except Exception as e:
            print(f"  {str(params):60s} → Exception: {e}")
    
    print("\n\n💡 Conclusion:")
    print("=" * 60)
    print("The API appears to only return current/today's period attendance.")
    print("Date parameters may not filter historical data.")
    print("\nFor historical data, you may need to:")
    print("  1. Run the script daily to accumulate data over time")
    print("  2. Check if there's a different API endpoint for historical data")
    print("  3. Contact ESD support about historical data access")

if __name__ == "__main__":
    main()
