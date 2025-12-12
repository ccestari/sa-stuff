# Firehose Delivery Diagnosis

## Issue
New webhooks are being received and sent to Firehose successfully, but not appearing in Redshift. Last data in Redshift is from December 5th.

## What's Working ✅
1. **API Gateway** - Receiving webhooks
2. **Lambda** - Processing and flattening JSON
3. **S3 Raw Storage** - Saving webhooks to `s3://edna-stream-meraki/raw/`
4. **Firehose PutRecord** - Lambda successfully sending to Firehose (confirmed with RecordId in logs)

## What's NOT Working ❌
5. **Firehose → Redshift Delivery** - Data not reaching Redshift table

## Evidence
- Lambda logs show: `✅ Firehose delivery: RecordId=xsnYgjaIWUksJAbOdsBUyDY9y0L3vmMB...`
- Firehose stream status: `ACTIVE`
- Firehose destination: `edna_stream_meraki.meraki_webhooks` in `db02` database
- S3 backup mode: `Disabled` (can't see delivery errors)
- Last Redshift data: December 5, 2025 (4 days ago)

## Root Cause
Firehose is likely failing to deliver to Redshift due to one of:
1. **Network connectivity** - Firehose can't reach Redshift cluster
2. **IAM permissions** - Firehose role lacks Redshift permissions
3. **Redshift cluster** - Cluster is paused or unavailable
4. **Table schema mismatch** - JSON doesn't match table structure
5. **COPY command failure** - Redshift COPY command failing silently

## Recommended Actions

### 1. Enable S3 Backup (CRITICAL)
This will let us see what Firehose is trying to deliver and any errors:
```bash
aws firehose update-destination \
  --delivery-stream-name meraki-redshift-stream \
  --current-delivery-stream-version-id <version> \
  --destination-id <destination-id> \
  --redshift-destination-update S3BackupMode=Enabled
```

### 2. Check Redshift Cluster Status
```bash
aws redshift describe-clusters \
  --cluster-identifier edna-prod-dw \
  --query 'Clusters[0].ClusterStatus'
```

### 3. Check Firehose IAM Role
The role needs:
- `redshift:DescribeClusters`
- `redshift:DescribeTable`
- `redshift:CopyFromS3`
- `s3:GetObject` on staging bucket
- `s3:PutObject` on backup bucket

### 4. Check Redshift STL_LOAD_ERRORS
```sql
SELECT 
    starttime,
    filename,
    line_number,
    colname,
    err_reason
FROM stl_load_errors
WHERE starttime >= CURRENT_DATE - 7
ORDER BY starttime DESC
LIMIT 20;
```

### 5. Manual Test
Send data directly to Redshift to verify connectivity:
```sql
COPY edna_stream_meraki.meraki_webhooks
FROM 's3://edna-stream-meraki/raw/2025-12-09-21-19-35-426a709b-0f27-4e09-98e6-7140d6be251e.json'
IAM_ROLE 'arn:aws:iam::309820967897:role/MerakiFirehoseRole'
JSON 'auto'
TIMEFORMAT 'auto'
TRUNCATECOLUMNS
BLANKSASNULL
EMPTYASNULL;
```

## Temporary Workaround
Until Firehose is fixed, webhooks are being saved to S3. We can manually load them:
```bash
# List recent webhooks
aws s3 ls s3://edna-stream-meraki/raw/ --recursive | grep "2025-12-09"

# Load manually (requires Redshift connection)
```

## Next Steps
1. Enable S3 backup on Firehose
2. Check Redshift cluster status
3. Review Firehose IAM role permissions
4. Check Redshift load errors
5. Test manual COPY command
