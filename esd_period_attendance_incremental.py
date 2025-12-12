#!/usr/bin/env python3
"""
Incremental ESD Period Attendance Fetcher
Runs continuously, fetching only missing data per school per day
"""
import boto3
import requests
import polars as pl
import json
import time
import sys
import os
from datetime import datetime
from collections import defaultdict
from io import BytesIO

sys.path.insert(0, '/Users/chris.cestari/Documents/GitHub/sa-stuff/sa-utils/aws-utils')
from credential_manager import CredentialManager

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

BASE_URL = "https://guru-ren.eschooldata.com:443/api"
SCHOOL_YEAR_ID = 55
PROGRESS_FILE = 'esd_fetch_progress.json'

def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {'completed': {}}

def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_esd_token(cred_mgr):
    """Get ESD OAuth token"""
    session = cred_mgr.get_session()
    client = session.client('secretsmanager')
    secret = client.get_secret_value(SecretId="prod/edna/esd_api_token")
    creds = json.loads(secret['SecretString'])
    response = requests.post(creds['ESD_URL'], data={
        'grant_type': 'client_credentials',
        'client_id': creds['ESD_CLIENT_ID'],
        'client_secret': creds['ESD_SECRET_KEY']
    })
    response.raise_for_status()
    return response.json()['access_token']

def fetch_schools(headers):
    """Fetch all schools"""
    all_schools = []
    page = 1
    while True:
        response = requests.get(f"{BASE_URL}/v1/schools", headers=headers, params={"pageSize": 1000, "page": page})
        response.raise_for_status()
        data = response.json()
        schools = data.get('schools', [])
        if not schools:
            break
        all_schools.extend(schools)
        paging = data.get('pagingInfo', {})
        if page >= paging.get('totalPages', 1):
            break
        page += 1
    return all_schools

def fetch_period_attendance(school_id, headers, cred_mgr):
    """Fetch period attendance for a school with token refresh"""
    all_records = []
    page = 1
    while True:
        try:
            response = requests.get(f"{BASE_URL}/v1/periodAttendance", headers=headers, 
                                  params={"schoolId": school_id, "schoolYearId": SCHOOL_YEAR_ID, 
                                         "pageSize": 1000, "page": page})
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token expired, refresh
                token = get_esd_token(cred_mgr)
                headers['Authorization'] = f"Bearer {token}"
                continue
            raise
        
        data = response.json()
        records = data.get('periodAttendanceList', [])
        if not records:
            break
        for record in records:
            record['schoolId'] = school_id
        all_records.extend(records)
        paging = data.get('pagingInfo', {})
        if page >= paging.get('pageCount', 1):
            break
        page += 1
    return all_records

def upload_to_s3(records, cred_mgr):
    """Upload records to S3 partitioned by date"""
    session = cred_mgr.get_session()
    s3 = session.client('s3')
    
    grouped = defaultdict(lambda: defaultdict(list))
    for record in records:
        school_id = record['schoolId']
        date_str = record['date']
        grouped[school_id][date_str].append(record)
    
    uploaded = 0
    for school_id, dates in grouped.items():
        for date_str, date_records in dates.items():
            month, day, year = date_str.split('-')
            
            # JSON
            json_key = f"raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/year={year}/month={month}/day={day}/school_{school_id}_{int(time.time())}.json"
            s3.put_object(Bucket='edna-prod', Key=json_key, Body=json.dumps(date_records))
            
            # Parquet
            try:
                df = pl.DataFrame(date_records)
                parquet_key = f"raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/year={year}/month={month}/day={day}/school_{school_id}_{int(time.time())}.parquet"
                buffer = BytesIO()
                df.write_parquet(buffer)
                buffer.seek(0)
                s3.put_object(Bucket='edna-prod', Key=parquet_key, Body=buffer.getvalue())
            except:
                pass
            
            uploaded += len(date_records)
    return uploaded

def main():
    print("="*70)
    print("ESD PERIOD ATTENDANCE INCREMENTAL FETCHER")
    print("="*70)
    
    # Load progress
    progress = load_progress()
    
    # Validate credentials
    print("\n[STEP 1] Validating AWS Credentials")
    print("-"*70)
    cred_mgr = CredentialManager('/Users/chris.cestari/Documents/GitHub/sa-stuff/credentials.yaml')
    cred_mgr.ensure_valid_credentials()
    
    # Get ESD token
    print("\n[STEP 2] Getting ESD OAuth Token")
    print("-"*70)
    token = get_esd_token(cred_mgr)
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Token obtained")
    
    # Fetch schools
    print("\n[STEP 3] Fetching Schools")
    print("-"*70)
    schools = fetch_schools(headers)
    print(f"✅ Found {len(schools)} schools")
    
    # Process each school
    print(f"\n[STEP 4] Processing Schools (School Year {SCHOOL_YEAR_ID})")
    print("-"*70)
    
    total_fetched = 0
    total_uploaded = 0
    schools_processed = 0
    
    for idx, school in enumerate(schools, 1):
        school_id = school.get('id')
        if not school_id:
            continue
        
        # Check if already completed
        if str(school_id) in progress['completed']:
            print(f"  [{idx}/{len(schools)}] School {school_id}... ⏭️  Already completed")
            continue
        
        try:
            print(f"  [{idx}/{len(schools)}] School {school_id}...", end=" ", flush=True)
            records = fetch_period_attendance(school_id, headers, cred_mgr)
            
            if records:
                uploaded = upload_to_s3(records, cred_mgr)
                total_fetched += len(records)
                total_uploaded += uploaded
                schools_processed += 1
                print(f"✅ {len(records)} records, {uploaded} uploaded")
                
                # Mark as completed
                progress['completed'][str(school_id)] = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'records': len(records)
                }
                save_progress(progress)
            else:
                print("⚠️  No records")
                progress['completed'][str(school_id)] = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'records': 0
                }
                save_progress(progress)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Schools processed:     {schools_processed}")
    print(f"Total records fetched: {total_fetched}")
    print(f"Total records uploaded: {total_uploaded}")
    print(f"Progress saved to:     {PROGRESS_FILE}")
    print("\n✅ COMPLETE!")
    print("="*70)

if __name__ == "__main__":
    main()
