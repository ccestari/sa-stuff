# Greenhouse Webhook Fix - COMPLETE

## ✅ DEPLOYED (Dec 8, 2025)

**Lambda:** `greenhouse-webhook-processor` - WORKING  
**Endpoint:** `https://kac177dcb8.execute-api.us-east-1.amazonaws.com/prod/webhook`  
**Status:** Returns HTTP 200 ✅

## Fixes Applied

1. Lambda handles None/empty body
2. Fixed context.aws_request_id
3. Added SQS permissions

## Pending

**Backfill:** Dec 5-8, 2025 data  
**Source:** s3://edna-dev-greenhouse-webhooks/webhook-data/ (nonprod 205372355929)  
**Target:** Redshift edna-prod-dw/db02/talent_acquisition.edna_stream_greenhouse (prod 309820967897)

## Tomorrow

1. Get fresh AWS credentials (both accounts)
2. Create backfill script
3. Load missing records
