# Greenhouse Webhook Streaming - Resume Instructions

## ✅ Current Status

**Webhook URL:** `https://kac177dcb8.execute-api.us-east-1.amazonaws.com/prod/webhook`

**Status:** WORKING (tested and confirmed returning HTTP 200)

## Step 1: Resume Greenhouse Webhook

Configure Greenhouse to send webhooks to:
```
https://kac177dcb8.execute-api.us-east-1.amazonaws.com/prod/webhook
```

The webhook is currently working and will accept data immediately.

## Step 2: Backfill Missing Data

Run the backfill script to copy missing records from raw_greenhouse to edna_stream_greenhouse:

```bash
cd /Users/chris.cestari/Documents/GitHub/sa-stuff/greenhouse-webhook-streaming
python3 backfill_from_raw.py
```

This will:
- Check for missing records between the two tables
- Show you how many records need to be backfilled
- Ask for confirmation before proceeding
- Copy all missing records

## Step 3: Update Lambda with Retry Logic (Optional)

To make the Lambda more resilient and return 500 errors to trigger Greenhouse retries:

```bash
python3 update_lambda_with_retry.py
```

This updates the Lambda to:
- Return HTTP 500 on any processing errors (triggers Greenhouse retry)
- Handle SQS failures gracefully
- Automatically recover from temporary issues

## Credential Management

### Check Credential Expiration
```bash
python3 check_credentials.py
```

### Update Credentials
When credentials expire (every ~30 minutes), update `credentials.yaml`:

```yaml
production:
  aws_access_key_id: YOUR_NEW_KEY
  aws_secret_access_key: YOUR_NEW_SECRET
  aws_session_token: YOUR_NEW_TOKEN
  account_id: "309820967897"
```

## Testing

Test the webhook anytime:
```bash
python3 test_webhook.py
```

Expected output: HTTP 200 with success message

## Monitoring

- **Lambda logs:** `/aws/lambda/greenhouse-webhook-processor`
- **SQS queue:** `greenhouse-flattened-records`
- **Redshift table:** `talent_acquisition.edna_stream_greenhouse.applications`

## Summary

1. ✅ Webhook is working: `https://kac177dcb8.execute-api.us-east-1.amazonaws.com/prod/webhook`
2. ⏳ Configure Greenhouse to use this URL
3. ⏳ Run `python3 backfill_from_raw.py` to fill missing data
4. ✅ Credentials updated and valid
5. ✅ Test script confirms webhook is operational
