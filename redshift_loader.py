#!/usr/bin/env python3
"""
Load period attendance data from S3 to Redshift
"""
import boto3
import psycopg2
from datetime import datetime

# AWS Credentials
AWS_ACCESS_KEY = "ASIAUQIWEZPMRGDKLUIK"
AWS_SECRET_KEY = "uX1DQgEBjjPNYAR4HKlJLn0fQTfF9ofb6cvfCAMT"
AWS_SESSION_TOKEN = "IQoJb3JpZ2luX2VjEP3//////////wEaCXVzLWVhc3QtMSJIMEYCIQCKxvJD4cRlTdIlL3TkCTLIIDHo/tF0WfF5JjT2dr3uHAIhAIaa4Vz321fjSC/i1rslh6y88sCt6UmWwK0E0bwLJQq+Kq0DCMb//////////wEQAxoMMzA5ODIwOTY3ODk3Igxzpw8YYrr8cR0IF3gqgQMwCpDmuznidK5KiGB7+9oNRaaaxntF0QKOmgvhfIgqLkD+h55XvcUtLYAB+KUfSEKzQn48res1rOIgFyLyynl75DJOqE8mEX5h5iywTgerW7GvJsBTtRiBtlQn3iZEs9x61IvMM25Zk9WmRacSK6U02XvSff/tc126c8Ab6udsgLolm53YPqfisp3xlNk7jCkvbPyjeTOC6jmFd3tsgDWz6a/+V5pIvind6TaYWxJ9KDywvHpXaWQFtylcqhwtt1Ls6oM7ZC8yONJYjavRjNEiuXftcCTxnDvoe+oQ8RgXrlRmGDm+PSLHW9a8kzD6k29VJGrERbLqa3YhWv+ppCp+lNyDY3TNFP2IyeoW9wW9XPQv8/2VfGXE9/zjOG2hMJwp7GjPs4L96ZBAExI5eBkZFVDjE554ZDRuwG8bkoss6nWXF/QB+zOxvwLpO+OaJ5lUP2VWbwstdoJe+qysw/uKZiJDYNnPBbozlpERTstSQp9mqLpx0lsHZw//qsGYh8XJML+P4skGOqMBQYt/zUYzn1GyA9+RJZeLKyNIESyVfM8moiUNZNBkljvOJrE1zaleKFVSI/CwM/ThdyTxmT2T51W+AWaz+78kFXrMBj0t88WXhFq1iQeg/IZCqMlU8Hx7PjS15UaaDEhxiWYqrjLNIAbEr1j5tbORTKtLGrTHxUZGnD5pYdoT0+yN3QKFAfmR5oD4MV3FkKp2/cINXXt9a3jZbspe3R61Wvto3Q=="

# Redshift Config (via SSH tunnel)
REDSHIFT_HOST = "localhost"  # SSH tunnel active
REDSHIFT_PORT = 5439
REDSHIFT_DB = "db02"
REDSHIFT_USER = "ccestari"
REDSHIFT_PASSWORD = "Cc@succ123!"

def get_s3_partitions(bucket: str, prefix: str):
    """List all date partitions in S3"""
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )
    
    partitions = set()
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            key = obj['Key']
            if 'year=' in key and 'month=' in key and 'day=' in key:
                parts = key.split('/')
                year_part = [p for p in parts if p.startswith('year=')][0]
                month_part = [p for p in parts if p.startswith('month=')][0]
                day_part = [p for p in parts if p.startswith('day=')][0]
                
                year = int(year_part.split('=')[1])
                month = int(month_part.split('=')[1])
                day = int(day_part.split('=')[1])
                
                partitions.add((year, month, day))
    
    return sorted(partitions)

def add_partition(conn, year: int, month: int, day: int):
    """Add partition to external table"""
    location = f"s3://edna-prod/raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/year={year}/month={month:02d}/day={day:02d}/"
    
    sql = f"""
    ALTER TABLE esd_spectrum.api_period_attendance 
    ADD IF NOT EXISTS PARTITION (year={year}, month={month}, day={day}) 
    LOCATION '{location}';
    """
    
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()
    
    print(f"  ✅ Added partition: year={year}, month={month}, day={day}")

def load_partition_to_redshift(conn, year: int, month: int, day: int):
    """Load data from external table partition to Redshift native table"""
    sql = f"""
    INSERT INTO ioesd.api_period_attendance
    SELECT 
        id,
        TO_DATE(date, 'MM-DD-YYYY') as attendance_date,
        studentId as student_id,
        meetingTimeId as meeting_time_id,
        meetingTime_sectionId as section_id,
        meetingTime_roomNumber as room_number,
        meetingTime_periodFrom as period_from,
        meetingTime_periodTo as period_to,
        meetingTime_startTime as start_time,
        meetingTime_endTime as end_time,
        attendanceReason as attendance_reason,
        modality,
        attendanceStatus as attendance_status,
        excusedStatus as excused_status,
        isEarlyDismissal as is_early_dismissal,
        minutesLate as minutes_late,
        minutesEarly as minutes_early,
        minutesMissed as minutes_missed,
        actualMinutes as actual_minutes,
        potentialMinutes as potential_minutes,
        CAST(createdOn AS TIMESTAMP) as created_on,
        CAST(modifiedOn AS TIMESTAMP) as modified_on,
        year,
        month,
        day
    FROM esd_spectrum.api_period_attendance
    WHERE year = {year} AND month = {month} AND day = {day}
    AND NOT EXISTS (
        SELECT 1 FROM ioesd.api_period_attendance p
        WHERE p.id = esd_spectrum.api_period_attendance.id
    );
    """
    
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.rowcount
        conn.commit()
    
    print(f"  ✅ Loaded {rows} records for {year}-{month:02d}-{day:02d}")
    return rows

def main():
    print("🔍 Discovering S3 partitions...")
    partitions = get_s3_partitions(
        'edna-prod',
        'raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/'
    )
    print(f"✅ Found {len(partitions)} partitions")
    
    print("\n🔐 Connecting to Redshift (via SSH tunnel)...")
    
    conn = psycopg2.connect(
        host=REDSHIFT_HOST,
        port=REDSHIFT_PORT,
        database=REDSHIFT_DB,
        user=REDSHIFT_USER,
        password=REDSHIFT_PASSWORD
    )
    print("✅ Connected to Redshift")
    
    print("\n📊 Adding partitions to external table...")
    for year, month, day in partitions:
        try:
            add_partition(conn, year, month, day)
        except Exception as e:
            print(f"  ⚠️  Partition {year}-{month:02d}-{day:02d} already exists or error: {e}")
    
    print("\n📥 Loading data to Redshift native table...")
    total_rows = 0
    for year, month, day in partitions:
        try:
            rows = load_partition_to_redshift(conn, year, month, day)
            total_rows += rows
        except Exception as e:
            print(f"  ❌ Error loading {year}-{month:02d}-{day:02d}: {e}")
    
    conn.close()
    print(f"\n✅ Complete! Loaded {total_rows} total records")

if __name__ == "__main__":
    main()
