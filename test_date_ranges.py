#!/usr/bin/env python3
"""
Test ESD API with different date ranges to find historical data
"""
import boto3
import requests
from datetime import datetime, timedelta

# AWS Credentials
AWS_ACCESS_KEY = "ASIAUQIWEZPMRGDKLUIK"
AWS_SECRET_KEY = "uX1DQgEBjjPNYAR4HKlJLn0fQTfF9ofb6cvfCAMT"
AWS_SESSION_TOKEN = "IQoJb3JpZ2luX2VjEP3//////////wEaCXVzLWVhc3QtMSJIMEYCIQCKxvJD4cRlTdIlL3TkCTLIIDHo/tF0WfF5JjT2dr3uHAIhAIaa4Vz321fjSC/i1rslh6y88sCt6UmWwK0E0bwLJQq+Kq0DCMb//////////wEQAxoMMzA5ODIwOTY3ODk3Igxzpw8YYrr8cR0IF3gqgQMwCpDmuznidK5KiGB7+9oNRaaaxntF0QKOmgvhfIgqLkD+h55XvcUtLYAB+KUfSEKzQn48res1rOIgFyLyynl75DJOqE8mEX5h5iywTgerW7GvJsBTtRiBtlQn3iZEs9x61IvMM25Zk9WmRacSK6U02XvSff/tc126c8Ab6udsgLolm53YPqfisp3xlNk7jCkvbPyjeTOC6jmFd3tsgDWz6a/+V5pIvind6TaYWxJ9KDywvHpXaWQFtylcqhwtt1Ls6oM7ZC8yONJYjavRjNEiuXftcCTxnDvoe+oQ8RgXrlRmGDm+PSLHW9a8kzD6k29VJGrERbLqa3YhWv+ppCp+lNyDY3TNFP2IyeoW9wW9XPQv8/2VfGXE9/zjOG2hMJwp7GjPs4L96ZBAExI5eBkZFVDjE554ZDRuwG8bkoss6nWXF/QB+zOxvwLpO+OaJ5lUP2VWbwstdoJe+qysw/uKZiJDYNnPBbozlpERTstSQp9mqLpx0lsHZw//qsGYh8XJML+P4skGOqMBQYt/zUYzn1GyA9+RJZeLKyNIESyVfM8moiUNZNBkljvOJrE1zaleKFVSI/CwM/ThdyTxmT2T51W+AWaz+78kFXrMBj0t88WXhFq1iQeg/IZCqMlU8Hx7PjS15UaaDEhxiWYqrjLNIAbEr1j5tbORTKtLGrTHxUZGnD5pYdoT0+yN3QKFAfmR5oD4MV3FkKp2/cINXXt9a3jZbspe3R61Wvto3Q=="

BASE_URL = "https://guru-ren.eschooldata.com:443/api"

def get_esd_credentials():
    """Get ESD credentials from AWS Secrets Manager"""
    client = boto3.client(
        'secretsmanager',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name='us-east-1'
    )
    secret = client.get_secret_value(SecretId="prod/edna/esd_api_token")
    import json
    creds = json.loads(secret['SecretString'])
    return creds

def get_esd_token():
    """Get OAuth token from ESD API"""
    creds = get_esd_credentials()
    token_url = creds['ESD_URL']
    client_id = creds['ESD_CLIENT_ID']
    secret = creds['ESD_SECRET_KEY']
    
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': secret
    }
    
    response = requests.post(token_url, data=payload)
    response.raise_for_status()
    token_data = response.json()
    return token_data['access_token']

def test_date_range(headers, school_id, start_date, end_date):
    """Test a specific date range"""
    params = {
        "pageSize": 100,
        "startDate": start_date,
        "endDate": end_date
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/v1/schools/{school_id}/periodAttendance",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        data = response.json()
        
        records = data if isinstance(data, list) else data.get('periodAttendance', [])
        return len(records), records
    except Exception as e:
        return 0, str(e)

def main():
    print("🔑 Getting OAuth token...")
    token = get_esd_token()
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Token obtained\n")
    
    # Test with school 12563 (had most records: 972)
    test_school = 12563
    
    # Test different date ranges
    today = datetime.now()
    
    date_ranges = [
        ("Today", today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")),
        ("Yesterday", (today - timedelta(days=1)).strftime("%Y-%m-%d"), (today - timedelta(days=1)).strftime("%Y-%m-%d")),
        ("Last 7 days", (today - timedelta(days=7)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")),
        ("Last 30 days", (today - timedelta(days=30)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")),
        ("Last 90 days", (today - timedelta(days=90)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")),
        ("This school year", "2024-08-01", today.strftime("%Y-%m-%d")),
        ("Last school year", "2023-08-01", "2024-06-30"),
        ("2 years ago", "2022-08-01", "2023-06-30"),
    ]
    
    print(f"📊 Testing date ranges for school {test_school}:\n")
    
    results = []
    for label, start, end in date_ranges:
        print(f"  Testing {label} ({start} to {end})...", end=" ")
        count, data = test_date_range(headers, test_school, start, end)
        
        if isinstance(data, str):
            print(f"❌ Error: {data}")
        else:
            print(f"✅ {count} records")
            if count > 0 and len(data) > 0:
                # Check unique dates in response
                dates = set()
                for record in data[:10]:  # Sample first 10
                    if 'date' in record:
                        dates.add(record['date'])
                if dates:
                    print(f"     Sample dates: {', '.join(sorted(dates)[:5])}")
        
        results.append((label, start, end, count))
    
    print("\n📈 Summary:")
    print("-" * 60)
    for label, start, end, count in results:
        print(f"  {label:20s} {start} to {end}: {count:5d} records")
    
    # Test without date parameters
    print("\n🔍 Testing without date parameters...")
    params = {"pageSize": 100}
    response = requests.get(
        f"{BASE_URL}/v1/schools/{test_school}/periodAttendance",
        headers=headers,
        params=params
    )
    data = response.json()
    records = data if isinstance(data, list) else data.get('periodAttendance', [])
    print(f"  ✅ {len(records)} records (no date filter)")
    
    if len(records) > 0:
        dates = set()
        for record in records[:20]:
            if 'date' in record:
                dates.add(record['date'])
        print(f"  Sample dates: {', '.join(sorted(dates)[:10])}")

if __name__ == "__main__":
    main()
