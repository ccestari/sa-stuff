# Backfill Data - TODO

## Task

Load missing Greenhouse webhook data from Dec 5-8, 2025.

## Data Locations

**Source (Backup):**
- Bucket: edna-dev-greenhouse-webhooks
- Prefix: webhook-data/
- Account: 205372355929 (nonprod)

**Target:**
- Cluster: edna-prod-dw
- Database: db02
- Schema: talent_acquisition.edna_stream_greenhouse
- Account: 309820967897 (prod)

## Steps

1. Get fresh AWS credentials (both accounts - expire every 30 min)
2. List S3 files in date range (Dec 5-8)
3. Create backfill script (Python or SQL)
4. Load records avoiding duplicates
5. Verify in Redshift

## SQL Approach (Recommended)

Run in Redshift Query Editor v2:

```sql
CREATE TEMP TABLE staging (webhook_data VARCHAR(MAX));

COPY staging
FROM 's3://edna-dev-greenhouse-webhooks/webhook-data/'
ACCESS_KEY_ID '<FRESH_KEY>'
SECRET_ACCESS_KEY '<FRESH_SECRET>'
SESSION_TOKEN '<FRESH_TOKEN>'
FORMAT AS JSON 'auto'
REGION 'us-east-1';

-- Insert avoiding duplicates
INSERT INTO talent_acquisition.edna_stream_greenhouse.applications
SELECT ... FROM staging WHERE NOT EXISTS ...;
```

## Python Approach

```python
import boto3, psycopg2, os

# Use environment variables
nonprod = boto3.Session(
    aws_access_key_id=os.environ['AWS_NONPROD_KEY'],
    aws_secret_access_key=os.environ['AWS_NONPROD_SECRET'],
    aws_session_token=os.environ['AWS_NONPROD_TOKEN']
)

conn = psycopg2.connect(
    host='edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com',
    port=5439,
    database='db02',
    user='ccestari',
    password=os.environ['REDSHIFT_PASSWORD']
)

# List, download, parse, insert
```

## Verification

```sql
SELECT COUNT(*) 
FROM talent_acquisition.edna_stream_greenhouse.applications
WHERE applied_at BETWEEN '2025-12-05 17:13' AND '2025-12-08 23:59';
```
