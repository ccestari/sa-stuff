#!/usr/bin/env python3
"""Backfill talent_acquisition.edna_stream_greenhouse from talent_acquisition.raw_greenhouse"""
import psycopg2
import yaml
import json
from datetime import datetime

print("=" * 60)
print("Greenhouse Data Backfill")
print("=" * 60)

# Load credentials
with open('credentials.yaml') as f:
    creds = yaml.safe_load(f)

with open('config.json') as f:
    config = json.load(f)

# Get Redshift password
redshift_password = input("Enter Redshift password: ")

# Connect to Redshift
print("\nConnecting to Redshift...")
conn = psycopg2.connect(
    host=config['redshift']['cluster_endpoint'],
    port=config['redshift']['cluster_port'],
    database=config['redshift']['database'],
    user=config['redshift']['admin_user'],
    password=redshift_password
)
conn.autocommit = False
cursor = conn.cursor()

# Get date range to backfill
print("\nChecking data gaps...")
cursor.execute("""
    SELECT 
        MIN(created_at) as earliest,
        MAX(created_at) as latest,
        COUNT(*) as count
    FROM talent_acquisition.raw_greenhouse
""")
raw_stats = cursor.fetchone()

cursor.execute("""
    SELECT 
        MIN(created_at) as earliest,
        MAX(created_at) as latest,
        COUNT(*) as count
    FROM talent_acquisition.edna_stream_greenhouse.applications
""")
stream_stats = cursor.fetchone()

print(f"\nRaw table: {raw_stats[2]:,} records ({raw_stats[0]} to {raw_stats[1]})")
print(f"Stream table: {stream_stats[2]:,} records ({stream_stats[0]} to {stream_stats[1]})")

# Find missing records
print("\nFinding missing records...")
cursor.execute("""
    SELECT COUNT(*)
    FROM talent_acquisition.raw_greenhouse r
    WHERE NOT EXISTS (
        SELECT 1 
        FROM talent_acquisition.edna_stream_greenhouse.applications s
        WHERE s.id = r.id
    )
""")
missing_count = cursor.fetchone()[0]

print(f"Missing records: {missing_count:,}")

if missing_count == 0:
    print("\n✅ No missing records - backfill not needed")
    cursor.close()
    conn.close()
    exit(0)

confirm = input(f"\nBackfill {missing_count:,} records? (yes/no): ")
if confirm.lower() != 'yes':
    print("Cancelled")
    cursor.close()
    conn.close()
    exit(0)

# Backfill
print("\nBackfilling...")
cursor.execute("""
    INSERT INTO talent_acquisition.edna_stream_greenhouse.applications
    SELECT * FROM talent_acquisition.raw_greenhouse r
    WHERE NOT EXISTS (
        SELECT 1 
        FROM talent_acquisition.edna_stream_greenhouse.applications s
        WHERE s.id = r.id
    )
""")

rows_inserted = cursor.rowcount
conn.commit()

print(f"\n✅ Backfill complete: {rows_inserted:,} records inserted")

cursor.close()
conn.close()
