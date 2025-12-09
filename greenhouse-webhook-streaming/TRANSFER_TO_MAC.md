# Transfer Instructions for Mac

## Files Successfully Fixed (Ready to Use)

All files in `greenhouse-webhook-streaming/` are ready except we can't push to GitHub due to old commits with credentials in history.

## What to Do Tomorrow on Mac

### Option 1: Manual Transfer (Simplest)
1. Copy the entire `greenhouse-webhook-streaming` folder to a USB drive or cloud storage
2. Transfer to Mac
3. Create new GitHub repo or push to a clean branch

### Option 2: Fresh Git Repo
```bash
# On Mac
cd ~/
mkdir greenhouse-webhook-streaming
# Copy files from Windows machine
# Then:
cd greenhouse-webhook-streaming
git init
git add .
git commit -m "Greenhouse webhook fix - clean history"
git remote add origin <your-repo-url>
git push -u origin main
```

## Key Files You Need

**Essential:**
- `lambda_function.py` - FIXED Lambda (already deployed to AWS)
- `HANDOFF_README.md` - Complete instructions
- `backfill_via_sql.sql` - SQL to backfill data
- `backfill_missing_data.py` - Python alternative
- `HTTP_500_ERROR_FIX.md` - Full documentation

**Supporting:**
- `add_sqs_permissions.py` - Already ran, SQS perms added
- `diagnose_500_error.py` - Diagnostic tool
- `config.json` - AWS configuration
- `requirements.txt` - Python dependencies

## What's Already Done ✅

1. Lambda function fixed and deployed
2. SQS permissions added to IAM role
3. Webhook returns HTTP 200 (tested)
4. All code cleaned of hardcoded credentials

## What Still Needs Doing

1. **Backfill missing data** (Dec 5-8)
   - Use `backfill_via_sql.sql` in Redshift Query Editor v2
   - OR run `backfill_missing_data.py` with fresh credentials

2. **Get fresh AWS credentials** (they expire every 30 min)
   - aws-nonproduction: 205372355929
   - aws-production: 309820967897

## Quick Start on Mac Tomorrow

```bash
# 1. Set up environment
pip3 install boto3 psycopg2-binary

# 2. Get fresh AWS credentials from SSO

# 3. Run backfill
# Either SQL in Redshift Query Editor v2
# OR
export AWS_NONPROD_ACCESS_KEY_ID=<key>
export AWS_NONPROD_SECRET_ACCESS_KEY=<secret>
export AWS_NONPROD_SESSION_TOKEN=<token>
export REDSHIFT_PASSWORD=<password>
python3 backfill_missing_data.py
```

## Credentials Needed Tomorrow

**AWS SSO:**
- Nonprod account (205372355929) - for S3 access
- Prod account (309820967897) - already have Redshift access

**Redshift:**
- Host: edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com
- Database: db02
- User: ccestari
- Password: (you know it)

## Summary

- ✅ HTTP 500 error FIXED
- ✅ Lambda deployed
- ✅ SQS permissions added
- ✅ Webhook working (HTTP 200)
- ⏳ Backfill pending (3 days of data)
- ⚠️ Can't push to GitHub (old commits have credentials)

**Solution:** Copy files manually or create fresh repo tomorrow.
