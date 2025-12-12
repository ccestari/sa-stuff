# Meraki Webhook Pipeline - Problem Diagnosis

## Current Status

### ✅ WORKING Components:
1. **Webhook Lambda** (`edna-meraki-iceberg-load-from-webhook`)
   - Receiving webhooks correctly
   - Sending data to Firehose
   
2. **Firehose** (`meraki-firehose`)
   - Receiving records from Lambda
   - Invoking transformation Lambda
   
3. **Transformation Lambda** (`firehose-data-transformation`)
   - Successfully processing records
   - Returns `'result': 'Ok'`
   - Transforms nested JSON to flat structure with 26 columns

### ❌ FAILING Component:
**Iceberg Table Write** - Data fails when Firehose tries to write to S3 Tables

## Evidence
- Files in `s3://edna-meraki-firehose-backup/iceberg-failed/` (most recent: Nov 19, 2025)
- Transformation Lambda logs show successful processing
- No data appearing in Iceberg table

## Root Cause (Most Likely)
**Schema Mismatch** between:
- Transformed data structure (26 columns from Lambda)
- Iceberg table schema in S3 Tables

## Transformed Data Structure
The transformation Lambda outputs these 26 fields:
```
alert_timestamp, alert_source, lambda_request_id, environment,
webhook_version, shared_secret, alert_sent_at, organization_id,
organization_name, organization_url, network_id, network_name,
network_url, network_tags, device_serial, device_mac, device_name,
device_url, device_tags, device_model, alert_id, alert_type,
alert_type_id, alert_level, alert_occurred_at, num
```

## Next Steps

### 1. Re-authenticate
```bash
aws sso login --profile AWSAdministratorAccess-309820967897
```

### 2. Run diagnosis
```bash
chmod +x final_diagnosis.sh
./final_diagnosis.sh
```

### 3. Compare schemas
Look for mismatches between:
- Transformed data fields (above)
- Iceberg table schema (from diagnosis output)

### 4. Likely Fixes

**Option A: Update Table Schema**
```bash
# Recreate table with correct schema matching the 26 columns
aws s3tables delete-table \
  --table-bucket-arn arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki \
  --namespace meraki_namespace \
  --name raw_meraki_payload \
  --region us-east-1

# Create with new schema (you'll need to define all 26 columns)
```

**Option B: Check Firehose Logs for Specific Error**
```bash
aws logs filter-log-events \
  --log-group-name /aws/kinesisfirehose/meraki-firehose \
  --log-stream-name-prefix DestinationDelivery \
  --start-time $(($(date +%s) - 86400))000 \
  --region us-east-1 \
  --filter-pattern "ERROR"
```

**Option C: Check Lake Formation Permissions**
Firehose role may lack permissions to write to S3 Tables

## Key Insight
The pipeline is 90% working. Only the final Iceberg write step is failing, likely due to schema mismatch or permissions.
