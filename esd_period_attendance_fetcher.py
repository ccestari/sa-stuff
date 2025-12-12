#!/usr/bin/env python3
"""
Fetch period attendance data from ESD API and upload to S3

S3 Convention:
  Path: raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/
        year=YYYY/month=MM/day=DD/
  Files: school_{schoolId}_{timestamp}.json
         school_{schoolId}_{timestamp}.parquet
  
  Example: year=2025/month=12/day=17/school_12345_1734456789.parquet
  
Column Names:
  - Preserves original API camelCase (studentId, meetingTimeId, etc.)
  - For snake_case conversion, use sa-utils/data-utils/column_transformers.py
"""
import boto3
import requests
import polars as pl
from datetime import datetime, timedelta
import time
import json
import sys
import os

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# AWS Credentials - loaded from credentials.yaml
AWS_ACCESS_KEY = None
AWS_SECRET_KEY = None
AWS_SESSION_TOKEN = None

token_expiry = None

# ESD API Config
BASE_URL = "https://guru-ren.eschooldata.com:443/api"

def prompt_aws_credentials():
    """Prompt user for AWS credentials"""
    global AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_SESSION_TOKEN
    print("\n⚠️  AWS credentials needed or expired")
    print("Please enter your AWS credentials:")
    AWS_ACCESS_KEY = input("AWS_ACCESS_KEY_ID: ").strip()
    AWS_SECRET_KEY = input("AWS_SECRET_ACCESS_KEY: ").strip()
    AWS_SESSION_TOKEN = input("AWS_SESSION_TOKEN: ").strip()
    print("✅ Credentials updated\n")

def validate_aws_credentials():
    """Validate AWS credentials by making a test call"""
    global AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_SESSION_TOKEN
    
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        return False
    
    try:
        client = boto3.client(
            'sts',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            aws_session_token=AWS_SESSION_TOKEN,
            region_name='us-east-1'
        )
        client.get_caller_identity()
        return True
    except Exception:
        return False

def get_esd_credentials():
    """Get ESD credentials from AWS Secrets Manager"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"  → Retrieving ESD credentials from Secrets Manager (attempt {attempt + 1}/{max_retries})...")
            client = boto3.client(
                'secretsmanager',
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                aws_session_token=AWS_SESSION_TOKEN,
                region_name='us-east-1'
            )
            secret = client.get_secret_value(SecretId="prod/edna/esd_api_token")
            creds = json.loads(secret['SecretString'])
            print("  ✅ ESD credentials retrieved")
            return creds
        except Exception as e:
            print(f"  ❌ Failed to get ESD credentials: {e}")
            if attempt < max_retries - 1:
                prompt_aws_credentials()
                if not validate_aws_credentials():
                    print("  ❌ Invalid AWS credentials")
                    continue
            else:
                raise

def get_esd_token():
    """Get OAuth token from ESD API"""
    global token_expiry
    print("  → Requesting OAuth token from ESD API...")
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
    token_expiry = time.time() + token_data.get('expires_in', 3600) - 300
    print(f"  ✅ OAuth token obtained (expires in {token_data.get('expires_in', 3600)}s)")
    return token_data['access_token'], token_data.get('expires_in', 3600)

def refresh_token_if_needed():
    """Check if token needs refresh"""
    global token_expiry
    if token_expiry and time.time() >= token_expiry:
        print("\n🔄 Token expiring, refreshing...")
        return get_esd_token()
    return None, None

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dict preserving original key names"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            # Convert all values to strings to avoid schema issues
            items.append((new_key, str(v) if v is not None else None))
    return dict(items)

def fetch_schools(headers: dict) -> list:
    """Fetch all schools with pagination"""
    print("  → Fetching schools from ESD API...")
    all_schools = []
    page = 1
    page_size = 1000
    
    while True:
        params = {"pageSize": page_size, "page": page}
        response = requests.get(f"{BASE_URL}/v1/schools", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        schools = data.get('schools', [])
        if not schools:
            break
            
        all_schools.extend(schools)
        print(f"  → Page {page}: {len(schools)} schools (total: {len(all_schools)})")
        
        paging = data.get('pagingInfo', {})
        if page >= paging.get('totalPages', 1):
            break
            
        page += 1
        
    return all_schools

def fetch_period_attendance(school_id: int, headers: dict, school_year_id: int = 55, page_size: int = 1000) -> list:
    """Fetch all period attendance for a school with pagination"""
    all_records = []
    page = 1
    
    while True:
        params = {"schoolId": school_id, "schoolYearId": school_year_id, "pageSize": page_size, "page": page, "sortField": "date", "sortDirection": "Ascending"}
            
        response = requests.get(
            f"{BASE_URL}/v1/periodAttendance",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        data = response.json()
        
        records = data if isinstance(data, list) else data.get('periodAttendanceList', [])
        if not records:
            break
        
        # Flatten and add schoolId to each record
        for record in records:
            flat_record = flatten_dict(record)
            flat_record['schoolId'] = school_id
            all_records.append(flat_record)
            
        if isinstance(data, dict):
            paging = data.get('pagingInfo', {})
            if page >= paging.get('pageCount', paging.get('totalPages', 1)):
                break
        else:
            if len(records) < page_size:
                break
                
        page += 1
        
    return all_records

def get_existing_s3_data(bucket: str, school_year_id: int = 55) -> set:
    """Get set of (school_id, date) tuples already in S3"""
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )
    
    existing = set()
    prefix = f"raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/"
    
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' not in page:
                continue
            for obj in page['Contents']:
                # Parse: schoolyear=55/schoolid=12345/month=12/day=17/
                parts = obj['Key'].split('/')
                school_part = [p for p in parts if p.startswith('schoolid=')]
                month_part = [p for p in parts if p.startswith('month=')]
                day_part = [p for p in parts if p.startswith('day=')]
                
                # Old format: year=2025/month=12/day=16/
                year_part = [p for p in parts if p.startswith('year=')]
                if year_part and month_part and day_part:
                    year = year_part[0].split('=')[1]
                    month = month_part[0].split('=')[1]
                    day = day_part[0].split('=')[1]
                    date_str = f"{month}-{day}-{year}"
                    # Extract school_id from filename if present
                    # For now, just track by date
                    existing.add(date_str)
    except Exception as e:
        print(f"  ⚠️  Error checking existing S3 data: {e}")
    
    return existing

def upload_to_s3_by_date(records: list, bucket: str, school_year_id: int = 55):
    """Upload data partitioned by school_id, then date in both JSON and Parquet"""
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )
    
    # Group by school_id and date
    from collections import defaultdict
    from io import BytesIO
    import json as json_lib
    
    grouped = defaultdict(lambda: defaultdict(list))
    for record in records:
        school_id = record['schoolId']
        date_str = record['date']  # MM-DD-YYYY
        grouped[school_id][date_str].append(record)
    
    for school_id, dates in grouped.items():
        for date_str, date_records in dates.items():
            # Parse date
            month, day, year = date_str.split('-')
            
            # JSON format
            json_key = f"raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/year={year}/month={month}/day={day}/school_{school_id}_{int(time.time())}.json"
            s3.put_object(Bucket=bucket, Key=json_key, Body=json_lib.dumps(date_records))
            
            # Parquet format
            try:
                df = pl.DataFrame(date_records)
                parquet_key = f"raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/year={year}/month={month}/day={day}/school_{school_id}_{int(time.time())}.parquet"
                buffer = BytesIO()
                df.write_parquet(buffer)
                buffer.seek(0)
                s3.put_object(Bucket=bucket, Key=parquet_key, Body=buffer.getvalue())
            except Exception as e:
                print(f"  ⚠️  Parquet error for school {school_id} | {date_str}: {e}")
            
            print(f"  ✅ School {school_id} | {date_str}: {len(date_records)} records")

def main():
    """Main execution"""
    global AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_SESSION_TOKEN
    
    print("="*70)
    print("ESD PERIOD ATTENDANCE FETCHER")
    print("="*70)
    
    # Load credentials from credentials.yaml
    import yaml
    try:
        with open('credentials.yaml') as f:
            creds = yaml.safe_load(f)
        prod_creds = creds['production']
        AWS_ACCESS_KEY = prod_creds['aws_access_key_id']
        AWS_SECRET_KEY = prod_creds['aws_secret_access_key']
        AWS_SESSION_TOKEN = prod_creds['aws_session_token']
    except FileNotFoundError:
        print("❌ credentials.yaml not found")
        return
    
    # Step 1: Validate AWS credentials
    print("\n[STEP 1/5] Validating AWS Credentials")
    print("-"*70)
    if not validate_aws_credentials():
        print("❌ AWS credentials invalid or missing")
        prompt_aws_credentials()
        if not validate_aws_credentials():
            print("❌ Still invalid. Exiting.")
            sys.exit(1)
    print("✅ AWS credentials valid")
    
    # Step 2: Get ESD OAuth token
    print("\n[STEP 2/5] Getting ESD OAuth Token")
    print("-"*70)
    token, expires = get_esd_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    school_year_id = 55
    print(f"\n📅 School Year ID: {school_year_id}")
    
    # Step 3: Fetch schools
    print("\n[STEP 3/5] Fetching Schools")
    print("-"*70)
    schools = fetch_schools(headers)
    print(f"✅ Found {len(schools)} schools")
    
    # Check existing S3 data
    print("\n  → Checking existing S3 data to skip duplicates...")
    existing_data = get_existing_s3_data("edna-prod", school_year_id=school_year_id)
    print(f"  ✅ Found {len(existing_data)} existing school/date combinations")
    if existing_data:
        sample = list(existing_data)[:3]
        print(f"  📋 Sample: {sample}")
    
    all_records = []
    batch_size = 5000
    page_size = 1000
    total_records_fetched = 0
    schools_with_data = 0
    schools_without_data = 0
    
    # Step 4: Fetch period attendance
    print(f"\n[STEP 4/5] Fetching Period Attendance Data")
    print("-"*70)
    print(f"Batch size: {batch_size} | Page size: {page_size}")
    print(f"Processing {len(schools)} schools...\n")
    
    for idx, school in enumerate(schools, 1):
        school_id = school.get('id')
        if not school_id:
            continue
        
        # Refresh token if needed
        new_token, _ = refresh_token_if_needed()
        if new_token:
            headers = {"Authorization": f"Bearer {new_token}"}
            print("✅ Token refreshed")
        
        try:
            print(f"  [{idx}/{len(schools)}] School {school_id}...", end=" ", flush=True)
            records = fetch_period_attendance(school_id, headers, school_year_id=school_year_id, page_size=page_size)
            
            if records and len(records) > 0:
                # Filter out records that already exist in S3
                new_records = []
                skipped = 0
                for record in records:
                    date_str = record.get('date')
                    if date_str not in existing_data:
                        new_records.append(record)
                    else:
                        skipped += 1
                
                if new_records:
                    all_records.extend(new_records)
                    total_records_fetched += len(new_records)
                    schools_with_data += 1
                    skip_msg = f" (skipped {skipped} existing)" if skipped > 0 else ""
                    print(f"✅ {len(new_records)} new records{skip_msg} (batch: {len(all_records)}, total: {total_records_fetched})")
                elif skipped > 0:
                    print(f"⏭️  All {skipped} records already in S3")
                else:
                    schools_without_data += 1
                    print("⚠️  No records")
                
                # Upload batch when reaching batch_size
                if len(all_records) >= batch_size:
                    print(f"\n  📦 BATCH UPLOAD: {len(all_records)} records")
                    print("  → Uploading to S3...")
                    upload_to_s3_by_date(all_records, "edna-prod", school_year_id=school_year_id)
                    all_records = []
                    print(f"  ✅ Batch uploaded successfully")
                    print(f"  📊 Progress: {schools_with_data} schools with data, {total_records_fetched} total records\n")
            else:
                schools_without_data += 1
                print("⚠️  No records")
            
            # Rate limiting
            time.sleep(0.5)
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print("⚠️  No records")
            elif e.response.status_code == 401:
                print("⚠️  Token expired, refreshing...")
                token, _ = get_esd_token()
                headers = {"Authorization": f"Bearer {token}"}
                continue
            else:
                print(f"❌ Error: {e}")
            time.sleep(1)
            continue
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
            continue
    
    # Step 5: Upload remaining records
    print(f"\n[STEP 5/5] Final Upload")
    print("-"*70)
    if all_records:
        print(f"📦 Uploading final batch of {len(all_records)} records...")
        upload_to_s3_by_date(all_records, "edna-prod", school_year_id=school_year_id)
        print("✅ Final batch uploaded")
    else:
        print("ℹ️  No remaining records to upload")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Schools processed:     {len(schools)}")
    print(f"Schools with data:     {schools_with_data}")
    print(f"Schools without data:  {schools_without_data}")
    print(f"Total records fetched: {total_records_fetched}")
    print("\n✅ COMPLETE! All schools processed.")
    print("="*70)

if __name__ == "__main__":
    main()
