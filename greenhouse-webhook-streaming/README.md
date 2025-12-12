# Greenhouse Webhook HTTP 500 Fix

## Status: ✅ DEPLOYED AND WORKING

**Fixed:** December 8, 2025  
**Lambda:** greenhouse-webhook-processor  
**Endpoint:** https://kac177dcb8.execute-api.us-east-1.amazonaws.com/prod/webhook  
**Region:** us-east-1  
**Account:** 309820967897

## Problem Solved

Greenhouse webhooks were failing with HTTP 500 errors since Dec 5, 2025 5:13 PM.

**Root Causes:**
1. Lambda crashed on None/empty body: `json.loads(None)` failed
2. Wrong context attribute: `context.request_id` should be `context.aws_request_id`
3. Missing SQS permissions on Lambda IAM role

**Solutions:**
1. ✅ Handle None/empty body gracefully
2. ✅ Fix context attribute references  
3. ✅ Add SQS permissions to `greenhouse-webhook-processor-role`
4. ✅ Deploy to production
5. ✅ Test - returns HTTP 200

## Files

- `lambda_function.py` - Deployed Lambda code (for reference)
- `STATUS.md` - Quick status summary
- `BACKFILL_TODO.md` - Instructions for data backfill

## Pending: Data Backfill

**Gap:** Dec 5, 2025 5:13 PM → Dec 8, 2025 11:59 PM  
**Source:** s3://edna-dev-greenhouse-webhooks/webhook-data/ (nonprod 205372355929)  
**Target:** Redshift edna-prod-dw → talent_acquisition.edna_stream_greenhouse (prod 309820967897)

## Test

```bash
curl -X POST https://kac177dcb8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" -d '{}'
```

Expected: `{"status": "success", "message": "Webhook received", "request_id": "..."}`

## Resources

**Lambda:** greenhouse-webhook-processor  
**SQS Queue:** greenhouse-flattened-records  
**CloudWatch:** /aws/lambda/greenhouse-webhook-processor  
**Redshift:** edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com:5439/db02

## Notes

- AWS credentials rotate every 30 minutes
- Never commit credentials to git
- Lambda is deployed - backfill is separate task
