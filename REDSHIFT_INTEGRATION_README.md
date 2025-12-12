# Period Attendance Redshift Integration

## Overview
This integration loads ESD period attendance data from S3 into Redshift for analytics.

## Architecture
```
ESD API → Python Script → S3 (Partitioned) → Redshift Spectrum → Redshift Native Table
```

## Components

### 1. Data Pipeline (`esd_period_attendance_fetcher.py`)
- Fetches period attendance from ESD API
- Flattens nested JSON structures
- **Partitions by date field** in records (not current date)
- Uploads to S3: `s3://edna-prod/raw_esd/incoming/periodAttendance/.../year=YYYY/month=MM/day=DD/`

### 2. Redshift Setup (`redshift_period_attendance_setup.sql`)
- Creates external schema `esd_spectrum` for S3 data access
- Creates external table `esd_spectrum.period_attendance` (partitioned)
- Creates native table `public.period_attendance` (optimized for queries)

### 3. Data Loader (`redshift_loader.py`)
- Discovers S3 partitions automatically
- Adds partitions to external table
- Loads data into native Redshift table
- Handles deduplication

## Redshift Cluster Info
- **Cluster**: edna-prod-dw
- **Endpoint**: edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com:5439
- **Database**: db02
- **User**: dba02
- **Node Type**: ra3.4xlarge (3 nodes)

## Prerequisites

### 1. IAM Role for Redshift Spectrum
Create IAM role with S3 read access:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::edna-prod/raw_esd/*",
        "arn:aws:s3:::edna-prod"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:CreateDatabase",
        "glue:DeleteDatabase",
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:UpdateDatabase",
        "glue:CreateTable",
        "glue:DeleteTable",
        "glue:BatchDeleteTable",
        "glue:UpdateTable",
        "glue:GetTable",
        "glue:GetTables",
        "glue:BatchCreatePartition",
        "glue:CreatePartition",
        "glue:DeletePartition",
        "glue:BatchDeletePartition",
        "glue:UpdatePartition",
        "glue:GetPartition",
        "glue:GetPartitions",
        "glue:BatchGetPartition"
      ],
      "Resource": "*"
    }
  ]
}
```

Attach to Redshift cluster:
```bash
aws redshift modify-cluster-iam-roles \
  --cluster-identifier edna-prod-dw \
  --add-iam-roles arn:aws:iam::309820967897:role/RedshiftSpectrumRole
```

### 2. Secrets Manager
Store Redshift password:
```bash
aws secretsmanager create-secret \
  --name prod/edna/redshift_credentials \
  --secret-string '{"password":"YOUR_PASSWORD"}'
```

### 3. Python Dependencies
```bash
pip install psycopg2-binary boto3 polars
```

## Usage

### Step 1: Fetch Data from ESD API
```bash
python esd_period_attendance_fetcher.py
```
This will:
- Fetch all period attendance records
- Partition by date field in records
- Upload to S3 with structure: `year=YYYY/month=MM/day=DD/`

### Step 2: Setup Redshift Tables (One-time)
```bash
psql -h edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com \
     -p 5439 -U dba02 -d db02 \
     -f redshift_period_attendance_setup.sql
```

### Step 3: Load Data to Redshift
```bash
python redshift_loader.py
```
This will:
- Discover all S3 partitions
- Add partitions to external table
- Load data into native Redshift table
- Skip duplicates

## Querying Data

### Query External Table (S3)
```sql
SELECT COUNT(*), year, month, day
FROM esd_spectrum.period_attendance
GROUP BY year, month, day
ORDER BY year DESC, month DESC, day DESC;
```

### Query Native Table (Redshift)
```sql
SELECT 
    attendance_date,
    COUNT(*) as total_records,
    COUNT(DISTINCT student_id) as unique_students,
    SUM(CASE WHEN attendance_status = 'Absent' THEN 1 ELSE 0 END) as absences
FROM public.period_attendance
WHERE attendance_date >= '2025-12-01'
GROUP BY attendance_date
ORDER BY attendance_date DESC;
```

## Performance Optimization

### Native Table Benefits
- **DISTKEY(student_id)**: Distributes data by student for efficient joins
- **SORTKEY(attendance_date, student_id)**: Optimizes date range queries
- **Compressed storage**: Better performance than S3 queries

### Incremental Loads
The loader script handles incremental loads:
- Only adds new partitions
- Deduplicates by `id` field
- Can be run daily/hourly

## Monitoring

### Check Partition Count
```sql
SELECT COUNT(DISTINCT year || '-' || month || '-' || day) as partition_count
FROM esd_spectrum.period_attendance;
```

### Check Data Freshness
```sql
SELECT MAX(attendance_date) as latest_date,
       MAX(modified_on) as latest_modified
FROM public.period_attendance;
```

### Check Row Counts
```sql
SELECT 
    'External' as source, COUNT(*) as row_count 
FROM esd_spectrum.period_attendance
UNION ALL
SELECT 
    'Native' as source, COUNT(*) as row_count 
FROM public.period_attendance;
```

## Troubleshooting

### Issue: "Spectrum Scan Error"
- Check IAM role has S3 access
- Verify S3 path exists and has data
- Check partition format matches table definition

### Issue: "Duplicate Key Violation"
- Loader script handles this automatically
- If manual insert, add `WHERE NOT EXISTS` clause

### Issue: "Date Parse Error"
- Verify date format is MM-DD-YYYY
- Check for NULL dates in source data

## Next Steps
1. Set up scheduled runs (cron/Airflow)
2. Add data quality checks
3. Create views for common queries
4. Set up monitoring/alerting
5. Add incremental update logic for modified records
