# Conversation Log - 2025-12-06

## Session Summary

Worked on getting Meraki webhook data flowing from S3 into Redshift after discovering Firehose wasn't loading data.

## Key Issues Resolved

### 1. Firehose Not Loading to Redshift
**Problem**: Firehose was configured with S3-only destination, not Redshift.
**Solution**: Recreated Firehose with Redshift destination using `recreate_firehose_redshift.py`

### 2. Firehose Still Not Loading
**Problem**: Firehose can't connect to Redshift (cluster behind VPN/bastion)
**Root Cause**: Redshift cluster requires VPN access, Firehose can't reach it
**Solution**: Manual COPY command from S3 to Redshift

### 3. IAM Role Not Associated
**Problem**: COPY command failed with "role not associated to cluster"
**Solution**: Use personal AWS credentials instead of IAM role in COPY command

### 4. Credentials Management
**Problem**: Scripts using different credential sources (env vars vs credentials.yaml)
**Solution**: Updated scripts to read directly from credentials.yaml

## Final Architecture

```
Meraki → API Gateway → Lambda → S3
                                  ↓
                            Manual COPY
                                  ↓
                              Redshift
```

## Commands That Work

### Check S3 Data
```bash
python check_s3_data.py
```

### Check Lambda Logs
```bash
python check_lambda_logs.py
```

### Load S3 to Redshift (VPN required)
```bash
python sync_s3_to_redshift.py  # Runs every 5 min
```

### Manual COPY (in Redshift Query Editor)
```sql
COPY edna_stream_meraki.meraki_webhooks (...)
FROM 's3://edna-stream-meraki/raw/'
ACCESS_KEY_ID '<key>'
SECRET_ACCESS_KEY '<secret>'
SESSION_TOKEN '<token>'
JSON 'auto' ...
```

## Test Results

- ✅ 11 webhooks successfully loaded to Redshift
- ✅ Lambda processing webhooks correctly
- ✅ S3 storing raw payloads
- ❌ Firehose can't auto-load to Redshift (VPN issue)

## Files Created/Modified

### New Files
- `recreate_firehose_redshift.py` - Recreate Firehose with Redshift
- `check_lambda_logs.py` - Check Lambda CloudWatch logs
- `check_firehose_logs.py` - Check Firehose logs
- `sync_s3_to_redshift.py` - Automated S3→Redshift sync
- `FINAL_STATUS.md` - Complete system status
- `CONVERSATION_LOG.md` - This file

### Modified Files
- `check_s3_data.py` - Updated to use credentials.yaml
- `credentials.yaml` - Updated with latest AWS credentials
- `lambda_function.py` - Attempted Redshift Data API (reverted)

## Lessons Learned

1. **Firehose requires direct network access** - Can't use with VPN-protected Redshift
2. **IAM roles must be associated with cluster** - Can't use arbitrary roles for COPY
3. **Personal credentials work for COPY** - Workaround for IAM role issue
4. **Manual COPY is viable** - Simple solution that works
5. **Credentials expire every 30 min** - Need to refresh frequently

## Next Steps for New Machine

1. Clone repo to macOS machine with VPN access
2. Install Python dependencies
3. Configure credentials.yaml
4. Run sync_s3_to_redshift.py
5. Keep running in background for continuous sync

## Credentials Used

- Production AWS: Account 309820967897
- Redshift: edna-prod-dw cluster
- Database: db02
- Schema: edna_stream_meraki
- SSH Bastion: 44.207.39.121

## Time Investment

- Troubleshooting Firehose: ~2 hours
- Testing COPY approaches: ~1 hour
- Creating sync solution: ~30 min
- Documentation: ~30 min
