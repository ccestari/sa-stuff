# ESD Period Attendance API - Findings

## Key Discovery

**The ESD API only returns current/today's period attendance data, regardless of date parameters.**

## Test Results

### Date Range Testing
Tested multiple date ranges with school 12563:
- Today (2025-12-09): 972 records ✅
- Yesterday (2025-12-08): 972 records (same data) ⚠️
- Last 7 days: 972 records (same data) ⚠️
- Last 30 days: 972 records (same data) ⚠️
- Last 90 days: 972 records (same data) ⚠️
- This school year (2024-08-01 to now): 972 records (same data) ⚠️
- Last school year (2023-08-01 to 2024-06-30): 972 records (same data) ⚠️
- 2 years ago: 972 records (same data) ⚠️

**All queries returned the exact same 972 records, all dated 12-09-2025.**

### Parameter Testing
Tested various parameter combinations:
- `startDate` / `endDate` - Ignored by API
- `fromDate` / `toDate` - Ignored by API
- `date` - Ignored by API
- `modifiedAfter` - Ignored by API

### Data Structure
```json
{
  "id": 5503183822,
  "date": "12-09-2025",
  "createdOn": "2025-12-04T03:26:58.23Z",
  "modifiedOn": "2025-12-09T08:01:44.337Z",
  "studentId": 41992,
  "meetingTimeId": 129019,
  "attendanceStatus": "A",
  ...
}
```

**Note**: `createdOn` is 2025-12-04, but `date` is 12-09-2025. This suggests:
- Records are created in advance
- The `date` field represents the attendance date
- API only returns records for "today"

## Implications

### For Historical Data Collection
❌ **Cannot fetch historical data via API date parameters**
✅ **Must run script daily to accumulate historical data**

### Current Pipeline Behavior
1. Script fetches all schools (89 found)
2. For each school, fetches period attendance
3. API returns only today's records
4. Data is partitioned by `date` field (currently only 12-09-2025)
5. Uploaded to S3: `year=2025/month=12/day=09/`

### Future Data Accumulation
Running the script daily will create:
```
s3://edna-prod/.../
  year=2025/month=12/day=09/  <- Today's run
  year=2025/month=12/day=10/  <- Tomorrow's run
  year=2025/month=12/day=11/  <- Next day's run
  ...
```

## Recommendations

### 1. Daily Scheduled Runs
Set up a daily cron job or scheduled task:
```bash
# Run at 11 PM daily (after school day ends)
0 23 * * * cd /path/to/scripts && python esd_period_attendance_fetcher.py
```

### 2. Check Existing Redshift Table
The existing `ioesd.periodattendance` table likely has historical data. Compare:
```sql
-- Check date range in existing table
SELECT 
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNT(*) as total_records,
    COUNT(DISTINCT date) as unique_dates
FROM ioesd.periodattendance;

-- Check if it has today's data
SELECT COUNT(*) 
FROM ioesd.periodattendance 
WHERE date = '2025-12-09';
```

### 3. Backfill Strategy
If historical data is needed:

**Option A**: Copy from existing table
```sql
-- Copy historical data to new API table
INSERT INTO ioesd.api_period_attendance
SELECT * FROM ioesd.periodattendance
WHERE date < CURRENT_DATE;
```

**Option B**: Contact ESD Support
- Ask about historical data API endpoint
- Request bulk export of historical period attendance
- Inquire about data retention policies

**Option C**: Use existing table
- Continue using `ioesd.periodattendance` for historical queries
- Use `ioesd.api_period_attendance` for new API-sourced data
- Create a view that unions both:
```sql
CREATE VIEW ioesd.period_attendance_complete AS
SELECT * FROM ioesd.periodattendance
WHERE date < '2025-12-09'
UNION ALL
SELECT * FROM ioesd.api_period_attendance;
```

## Production Setup

### Daily Pipeline
```
┌─────────────────┐
│  Cron Job       │  11 PM daily
│  (23:00)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch Script   │  Get today's data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  S3 Partition   │  year=YYYY/month=MM/day=DD/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redshift Load  │  Load new partition
└─────────────────┘
```

### Monitoring
- Check for daily run completion
- Alert if no new partition created
- Monitor record counts per day
- Compare with existing table counts

### Data Quality Checks
```sql
-- Check for missing dates
WITH date_series AS (
    SELECT GENERATE_SERIES(
        '2025-12-09'::DATE,
        CURRENT_DATE,
        '1 day'::INTERVAL
    )::DATE as check_date
)
SELECT check_date
FROM date_series
WHERE check_date NOT IN (
    SELECT DISTINCT attendance_date 
    FROM ioesd.api_period_attendance
)
ORDER BY check_date;

-- Check for duplicate records
SELECT 
    id, 
    COUNT(*) as count
FROM ioesd.api_period_attendance
GROUP BY id
HAVING COUNT(*) > 1;
```

## Next Steps

1. ✅ **Confirmed**: Date-based partitioning works correctly
2. ✅ **Confirmed**: API only returns today's data
3. ⏳ **TODO**: Set up daily scheduled run
4. ⏳ **TODO**: Check existing `ioesd.periodattendance` for historical data
5. ⏳ **TODO**: Decide on backfill strategy
6. ⏳ **TODO**: Set up monitoring and alerts
7. ⏳ **TODO**: Create Redshift tables and views

## Questions for ESD Support

1. Is there an API endpoint for historical period attendance data?
2. What is the data retention policy for the period attendance API?
3. Can we get a bulk export of historical data?
4. Are there any undocumented parameters for date filtering?
5. Is the current behavior (only today's data) intentional?

## Summary

✅ **Pipeline is working correctly**
✅ **Date-based partitioning is functional**
⚠️ **API limitation**: Only returns current day's data
💡 **Solution**: Run daily to accumulate historical data over time
📊 **Alternative**: Use existing `ioesd.periodattendance` table for historical analysis
