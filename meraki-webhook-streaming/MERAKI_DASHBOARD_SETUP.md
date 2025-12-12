# Meraki Dashboard Webhook Setup

## Correct Webhook URL

```
https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook
```

**IMPORTANT**: Must include `/webhook` at the end!

## Setup Steps

1. **Log into Meraki Dashboard**
   - Go to your organization

2. **Navigate to Alerts**
   - Click **Network-wide** → **Alerts**
   - Scroll down to **Webhooks** section

3. **Add HTTP Server**
   - Click **Add an HTTP server**
   
4. **Configure Webhook**
   - **Name**: `AWS Redshift Webhook` (or any name you choose)
   - **URL**: `https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook`
   - **Shared secret**: Enter any value (e.g., `meraki123` or leave as nonsense)
   
5. **Test Webhook**
   - Click **Send test webhook**
   - Should see success message

6. **Select Alert Types**
   - Choose which alerts to send:
     - ✅ Sensor alerts (temperature, humidity, water, door)
     - ✅ Motion alerts
     - ✅ Device status alerts (up/down)
     - ✅ Power supply alerts
     - ✅ Network alerts

7. **Save Configuration**

## Troubleshooting

### Test Webhook Fails

**Common Issues:**
- ❌ Missing `/webhook` at end of URL
- ❌ Using wrong API Gateway ID (use `db8pogv7q9`, not `o4wv2w79ha`)
- ❌ Typo in URL

**Correct URL Format:**
```
https://[API_GATEWAY_ID].execute-api.us-east-1.amazonaws.com/prod/webhook
```

### Verify URL Works

Test from command line:
```bash
python3 test_webhook.py --url https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook
```

Should return:
```
✅ Success: 200
```

## What Happens After Setup

1. Meraki sends webhooks to API Gateway
2. Lambda processes and stores to S3
3. Data flows to Redshift
4. View data in `edna_stream_meraki.meraki_webhooks` table

## Verify Data Flow

```bash
# Check S3 for new webhooks
python3 check_s3_data.py

# Check Lambda logs
python3 check_lambda_logs.py
```

## Quick Reference

| Field | Value |
|-------|-------|
| **URL** | `https://db8pogv7q9.execute-api.us-east-1.amazonaws.com/prod/webhook` |
| **Shared Secret** | Any value (not validated currently) |
| **Method** | POST (automatic) |
| **Content-Type** | application/json (automatic) |
