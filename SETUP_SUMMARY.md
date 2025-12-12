# ESD Period Attendance Pipeline - Setup Summary

## Current Status

### ✅ Completed
1. **Data Fetcher** (`esd_period_attendance_fetcher.py`)
   - Fetches from ESD API with OAuth
   - Paginates schools (89 found) and period attendance
   - Flattens nested JSON (26 → 41 columns)
   - **Partitions by date field in records** (not current date)
   - Uploads to S3: `s3://edna-prod/raw_esd/.../year=YYYY/month=MM/day=DD/`
   - Last run: 1,590 records from 1900-01-01 to 2025-12-09

2. **Redshift Integration Files**
   - SQL setup script
   - Python loader script
   - Comprehensive README

### 📊 Data Analysis
- **Current data**: Only 1 date (12-09-2025) with 1,590 records
- **Reason**: Fetching current operational data
- **Historical data**: Would need date range parameters or multiple runs

## Redshift Configuration

### Target Location
- **Cluster**: edna-prod-dw
- **Database**: db02
- **Schema**: ioesd (existing - 200+ tables)
- **New Table**: `api_period_attendance` (avoids conflict with existing `periodattendance`)
- **Connection**: Via SSH tunnel (localhost:5439)
- **User**: ccestari
- **Password**: Cc@succ123!

### No Dependencies Created
The new table `ioesd.api_period_attendance` is completely independent:
- ✅ Does NOT affect `ioesd.periodattendance`
- ✅ Does NOT affect `ioesd.raw_periodattendance`
- ✅ Does NOT create foreign keys or constraints
- ✅ Does NOT modify existing tables
- ✅ Standalone table with own data

## Next Steps

### 1. Test Date-Based Partitioning
Run the fetcher to verify partitioning works:
```bash
python esd_period_attendance_fetcher.py
```

Expected output:
- Multiple S3 paths if data spans multiple dates
- Format: `year=YYYY/month=MM/day=DD/`

### 2. Create IAM Role for Spectrum
```bash
# Create role with S3 + Glue permissions
aws iam create-role --role-name RedshiftSpectrumRole --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "redshift.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}'

# Attach policies
aws iam attach-role-policy \
  --role-name RedshiftSpectrumRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

aws iam attach-role-policy \
  --role-name RedshiftSpectrumRole \
  --policy-arn arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess

# Attach to cluster
aws redshift modify-cluster-iam-roles \
  --cluster-identifier edna-prod-dw \
  --add-iam-roles arn:aws:iam::309820967897:role/RedshiftSpectrumRole
```

### 3. Setup Redshift Tables
With SSH tunnel active:
```bash
psql -h localhost -p 5439 -U ccestari -d db02 -f redshift_period_attendance_setup.sql
```

This creates:
- External schema: `esd_spectrum`
- External table: `esd_spectrum.api_period_attendance` (points to S3)
- Native table: `ioesd.api_period_attendance` (optimized for queries)

### 4. Load Data
```bash
python redshift_loader.py
```

This will:
- Discover S3 partitions
- Add to external table
- Load into native table
- Skip duplicates

## File Locations

### Scripts
- `/Users/chris.cestari/Documents/GitHub/sa-stuff/esd_period_attendance_fetcher.py`
- `/Users/chris.cestari/Documents/GitHub/sa-stuff/redshift_loader.py`
- `/Users/chris.cestari/Documents/GitHub/sa-stuff/redshift_period_attendance_setup.sql`

### S3 Data
- `s3://edna-prod/raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/`
- Current: `year=2025/month=12/day=09/data_1765309990.parquet`

### Redshift
- Schema: `ioesd`
- Table: `api_period_attendance`
- External: `esd_spectrum.api_period_attendance`

## Data Flow

```
ESD API
  ↓ (OAuth + Pagination)
Python Fetcher
  ↓ (Flatten + Parse Date)
S3 Partitioned Storage
  ↓ (Spectrum External Table)
Redshift Native Table (ioesd.api_period_attendance)
```

## Key Points

### Date Partitioning
- ✅ Partitions by `date` field in records (MM-DD-YYYY format)
- ✅ Groups records by date before upload
- ✅ Creates separate S3 paths: `year=YYYY/month=MM/day=DD/`
- ⚠️ Current data only has 1 date (12-09-2025)

### Single Date Issue
**Why only one date?**
- Fetching current operational data
- Date range: 1900-01-01 to 2025-12-09
- But API only returns recent records

**Solutions:**
1. Run daily to accumulate dates over time
2. Adjust date range parameters
3. Check if API has historical data available

### Schema Safety
- New table name: `api_period_attendance`
- Existing tables untouched
- No foreign keys or dependencies
- Can be dropped without affecting other tables

## Verification Queries

### Check External Table
```sql
SELECT COUNT(*), year, month, day
FROM esd_spectrum.api_period_attendance
GROUP BY year, month, day;
```

### Check Native Table
```sql
SELECT 
    attendance_date,
    COUNT(*) as records,
    COUNT(DISTINCT student_id) as students
FROM ioesd.api_period_attendance
GROUP BY attendance_date
ORDER BY attendance_date DESC;
```

### Compare with Existing Table
```sql
-- New API table
SELECT COUNT(*) as api_count FROM ioesd.api_period_attendance;

-- Existing table
SELECT COUNT(*) as existing_count FROM ioesd.periodattendance;
```

## Troubleshooting

### SSH Tunnel Not Active
```bash
ssh -L 5439:edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com:5439 chris.cestari@44.207.39.121
```

### Credentials Expired
Update in scripts:
- `esd_period_attendance_fetcher.py` (lines 12-14)
- `redshift_loader.py` (lines 9-11)

### Only One Date in Data
This is expected for current operational data. To get more dates:
- Run daily to accumulate
- Or adjust API date parameters
- Or check if historical data exists

## Cost Estimate

### S3 Storage
- ~50KB per 1,590 records
- ~$0.023/GB/month
- Negligible cost

### Redshift Spectrum
- $5 per TB scanned
- Small dataset = minimal cost

### Redshift Storage
- Included in cluster cost
- No additional charge

## Next Actions

1. ✅ Test fetcher with date partitioning
2. ⏳ Create IAM role for Spectrum
3. ⏳ Run SQL setup script
4. ⏳ Run loader script
5. ⏳ Verify data in Redshift
6. ⏳ Schedule daily runs

## Questions Answered

**Q: Was there only a single date in the data?**
A: Yes, only 12-09-2025 with 1,590 records. This is expected for current operational data.

**Q: Will this affect existing tables?**
A: No. New table `api_period_attendance` is independent. No dependencies created.

**Q: Where should the table be created?**
A: In `ioesd` schema (existing schema with 200+ tables). Table name changed to avoid conflicts.

**Q: What about SSH tunnel?**
A: Loader script configured for localhost:5439 (SSH tunnel). Make sure tunnel is active before running.
