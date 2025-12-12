# Meraki Webhook Pipeline Troubleshooting

## Problem Summary
Data from Meraki webhooks is reaching Firehose but failing to load into the S3 Iceberg table.

## Evidence
- ✅ Lambda webhook handler is configured correctly
- ✅ Firehose is receiving data (files in S3 backup bucket)
- ❌ Data is failing at two points:
  - `processing-failed/` - Transformation Lambda failures
  - `iceberg-failed/` - Iceberg write failures

## Pipeline Flow
```
Webhook → API Gateway → Lambda (edna-meraki-iceberg-load-from-webhook) 
  → Firehose (meraki-firehose) → Transformation Lambda (firehose-data-transformation)
  → S3 Tables Iceberg (lakehouse-meraki/meraki_namespace/raw_meraki_payload)
```

## Diagnostic Scripts

### 1. Re-authenticate
```bash
aws sso login --profile AWSAdministratorAccess-309820967897
```

### 2. Run comprehensive diagnosis
```bash
chmod +x diagnose_and_fix.sh
./diagnose_and_fix.sh
```

### 3. Test with real payload
```bash
./test_with_real_payload.sh
```

### 4. Check table schema
```bash
./check_table_schema.sh
```

## Common Issues & Fixes

### Issue 1: Transformation Lambda Failing
**Symptoms:** Files in `processing-failed/`
**Check:** Lambda logs for errors
**Fix:** Update transformation Lambda code to handle payload structure

### Issue 2: Schema Mismatch
**Symptoms:** Files in `iceberg-failed/`
**Check:** S3 Tables schema vs actual data structure
**Fix:** Update table schema or transform data to match

### Issue 3: Permission Issues
**Symptoms:** Access denied errors in logs
**Check:** IAM roles for Firehose and Lambda
**Fix:** Add missing permissions

### Issue 4: No Data Flowing
**Symptoms:** No files in S3 backup bucket
**Check:** API Gateway → Lambda connection
**Fix:** Verify API Gateway trigger and Lambda permissions

## Next Steps

1. Run `./diagnose_and_fix.sh` after re-authenticating
2. Review transformation Lambda logs for specific errors
3. Compare payload structure with table schema
4. Fix transformation Lambda or update schema
5. Test with `./test_with_real_payload.sh`
