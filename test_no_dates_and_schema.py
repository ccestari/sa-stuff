#!/usr/bin/env python3
"""
Test API without date parameters and compare schemas
"""
import boto3
import requests
import psycopg2
import json

# AWS Credentials
AWS_ACCESS_KEY = "ASIAUQIWEZPMRGDKLUIK"
AWS_SECRET_KEY = "uX1DQgEBjjPNYAR4HKlJLn0fQTfF9ofb6cvfCAMT"
AWS_SESSION_TOKEN = "IQoJb3JpZ2luX2VjEP3//////////wEaCXVzLWVhc3QtMSJIMEYCIQCKxvJD4cRlTdIlL3TkCTLIIDHo/tF0WfF5JjT2dr3uHAIhAIaa4Vz321fjSC/i1rslh6y88sCt6UmWwK0E0bwLJQq+Kq0DCMb//////////wEQAxoMMzA5ODIwOTY3ODk3Igxzpw8YYrr8cR0IF3gqgQMwCpDmuznidK5KiGB7+9oNRaaaxntF0QKOmgvhfIgqLkD+h55XvcUtLYAB+KUfSEKzQn48res1rOIgFyLyynl75DJOqE8mEX5h5iywTgerW7GvJsBTtRiBtlQn3iZEs9x61IvMM25Zk9WmRacSK6U02XvSff/tc126c8Ab6udsgLolm53YPqfisp3xlNk7jCkvbPyjeTOC6jmFd3tsgDWz6a/+V5pIvind6TaYWxJ9KDywvHpXaWQFtylcqhwtt1Ls6oM7ZC8yONJYjavRjNEiuXftcCTxnDvoe+oQ8RgXrlRmGDm+PSLHW9a8kzD6k29VJGrERbLqa3YhWv+ppCp+lNyDY3TNFP2IyeoW9wW9XPQv8/2VfGXE9/zjOG2hMJwp7GjPs4L96ZBAExI5eBkZFVDjE554ZDRuwG8bkoss6nWXF/QB+zOxvwLpO+OaJ5lUP2VWbwstdoJe+qysw/uKZiJDYNnPBbozlpERTstSQp9mqLpx0lsHZw//qsGYh8XJML+P4skGOqMBQYt/zUYzn1GyA9+RJZeLKyNIESyVfM8moiUNZNBkljvOJrE1zaleKFVSI/CwM/ThdyTxmT2T51W+AWaz+78kFXrMBj0t88WXhFq1iQeg/IZCqMlU8Hx7PjS15UaaDEhxiWYqrjLNIAbEr1j5tbORTKtLGrTHxUZGnD5pYdoT0+yN3QKFAfmR5oD4MV3FkKp2/cINXXt9a3jZbspe3R61Wvto3Q=="

BASE_URL = "https://guru-ren.eschooldata.com:443/api"

def get_esd_token():
    client = boto3.client(
        'secretsmanager',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name='us-east-1'
    )
    secret = client.get_secret_value(SecretId="prod/edna/esd_api_token")
    creds = json.loads(secret['SecretString'])
    
    payload = {
        'grant_type': 'client_credentials',
        'client_id': creds['ESD_CLIENT_ID'],
        'client_secret': creds['ESD_SECRET_KEY']
    }
    response = requests.post(creds['ESD_URL'], data=payload)
    response.raise_for_status()
    return response.json()['access_token']

def test_api_without_dates():
    """Test API call WITHOUT any date parameters"""
    print("🔍 Testing API WITHOUT date parameters")
    print("=" * 60)
    
    token = get_esd_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    school_id = 12563  # School with most records
    
    # Test 1: Only pageSize
    print("\n1. With ONLY pageSize parameter:")
    params = {"pageSize": 1000}
    response = requests.get(
        f"{BASE_URL}/v1/schools/{school_id}/periodAttendance",
        headers=headers,
        params=params
    )
    data = response.json()
    records = data if isinstance(data, list) else data.get('periodAttendance', [])
    
    print(f"   Records returned: {len(records)}")
    
    if len(records) > 0:
        dates = {}
        for record in records:
            date = record.get('date')
            dates[date] = dates.get(date, 0) + 1
        
        print(f"   Unique dates: {len(dates)}")
        print(f"   Date distribution:")
        for date, count in sorted(dates.items())[:10]:
            print(f"     {date}: {count} records")
    
    # Test 2: No parameters at all
    print("\n2. With NO parameters:")
    response = requests.get(
        f"{BASE_URL}/v1/schools/{school_id}/periodAttendance",
        headers=headers
    )
    data = response.json()
    records = data if isinstance(data, list) else data.get('periodAttendance', [])
    print(f"   Records returned: {len(records)}")
    
    return records

def compare_schemas():
    """Compare schemas between tables"""
    print("\n\n📊 Comparing Redshift Table Schemas")
    print("=" * 60)
    
    conn = psycopg2.connect(
        host='localhost',
        port=5439,
        database='db02',
        user='ccestari',
        password='Cc@succ123!'
    )
    cur = conn.cursor()
    
    tables = ['periodattendance', 'raw_periodattendance', 'prod_periodattendance']
    
    for table in tables:
        print(f"\n{table}:")
        print("-" * 60)
        
        # Check if table exists
        cur.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'ioesd' 
            AND table_name = '{table}'
        """)
        
        if cur.fetchone()[0] == 0:
            print(f"  ⚠️  Table does not exist")
            continue
        
        # Get columns
        cur.execute(f"""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'ioesd' 
            AND table_name = '{table}'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        print(f"  Columns: {len(columns)}")
        
        # Show date-related columns
        date_cols = [c for c in columns if 'date' in c[0].lower() or 'time' in c[0].lower() or 'modified' in c[0].lower() or 'created' in c[0].lower()]
        if date_cols:
            print(f"\n  Date/Time columns:")
            for col_name, data_type, max_len in date_cols:
                print(f"    {col_name:30s} {data_type}")
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM ioesd.{table}")
        row_count = cur.fetchone()[0]
        print(f"\n  Total rows: {row_count:,}")
        
        # Get date range
        if any('date' in c[0].lower() for c in columns):
            date_col = next((c[0] for c in columns if c[0] == 'date'), None)
            if date_col:
                cur.execute(f"""
                    SELECT 
                        MIN({date_col}) as min_date,
                        MAX({date_col}) as max_date,
                        COUNT(DISTINCT {date_col}) as unique_dates
                    FROM ioesd.{table}
                """)
                min_date, max_date, unique_dates = cur.fetchone()
                print(f"  Date range: {min_date} to {max_date}")
                print(f"  Unique dates: {unique_dates:,}")
    
    conn.close()

def check_modified_vs_date():
    """Check if modified dates differ from attendance dates"""
    print("\n\n🔍 Checking Modified vs Attendance Dates")
    print("=" * 60)
    
    conn = psycopg2.connect(
        host='localhost',
        port=5439,
        database='db02',
        user='ccestari',
        password='Cc@succ123!'
    )
    cur = conn.cursor()
    
    # Check periodattendance table
    print("\nChecking ioesd.periodattendance:")
    
    # Get column names first
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns
        WHERE table_schema = 'ioesd' 
        AND table_name = 'periodattendance'
        AND (column_name LIKE '%date%' OR column_name LIKE '%modified%' OR column_name LIKE '%created%')
        ORDER BY ordinal_position
    """)
    
    date_columns = [row[0] for row in cur.fetchall()]
    print(f"  Date/time columns: {', '.join(date_columns)}")
    
    # Check for records where modified date != attendance date
    if 'date' in date_columns and 'modifiedon' in date_columns:
        cur.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN DATE(modifiedon) != date THEN 1 END) as different_dates,
                MIN(date) as min_attendance_date,
                MAX(date) as max_attendance_date,
                MIN(modifiedon) as min_modified,
                MAX(modifiedon) as max_modified
            FROM ioesd.periodattendance
            WHERE date IS NOT NULL AND modifiedon IS NOT NULL
        """)
        
        result = cur.fetchone()
        total, different, min_att, max_att, min_mod, max_mod = result
        
        print(f"\n  Total records: {total:,}")
        print(f"  Records where modified date != attendance date: {different:,} ({100*different/total if total > 0 else 0:.1f}%)")
        print(f"  Attendance date range: {min_att} to {max_att}")
        print(f"  Modified date range: {min_mod} to {max_mod}")
        
        # Sample records with different dates
        if different > 0:
            cur.execute("""
                SELECT date, modifiedon, createdon
                FROM ioesd.periodattendance
                WHERE DATE(modifiedon) != date
                LIMIT 5
            """)
            
            print(f"\n  Sample records with different dates:")
            for att_date, mod_date, created_date in cur.fetchall():
                print(f"    Attendance: {att_date}, Modified: {mod_date}, Created: {created_date}")
    
    conn.close()

def main():
    print("🔑 Getting OAuth token...")
    
    # Test 1: API without dates
    records = test_api_without_dates()
    
    # Test 2: Compare schemas
    compare_schemas()
    
    # Test 3: Check modified vs date
    check_modified_vs_date()
    
    print("\n\n💡 Summary:")
    print("=" * 60)
    print("1. API behavior confirmed (with/without date params)")
    print("2. Schema comparison completed")
    print("3. Modified date analysis completed")
    print("\nFor Iceberg/Delta Lake consideration:")
    print("  - Check if modified dates differ significantly from attendance dates")
    print("  - If yes, CDC (Change Data Capture) would be beneficial")
    print("  - Iceberg/Delta would enable time travel and incremental updates")

if __name__ == "__main__":
    main()
