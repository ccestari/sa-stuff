# Meraki Webhook Streaming - Deployment Guide

Complete step-by-step guide to deploy the Meraki webhook streaming solution.

## Overview

This guide walks you through deploying a complete webhook streaming pipeline from Meraki Dashboard to AWS Redshift.

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] AWS CLI configured (optional)
- [ ] Access to AWS Account 309820967897
- [ ] Redshift credentials for ccestari user
- [ ] SSH access to bastion host (44.207.39.121)
- [ ] Meraki Dashboard admin access

## Phase 1: Environment Setup

### 1.1 Install Python Dependencies

```bash
cd c:\Users\cesta\OneDrive\Documents\GitHub\sa-stuff\meraki-webhook-streaming
pip install -r requirements.txt
```

Expected output:
```
Successfully installed boto3-1.34.x botocore-1.34.x psycopg2-binary-2.9.x ...
```

### 1.2 Setup AWS Credentials

Get fresh credentials from AWS SSO:
1. Visit: https://d-9067640efb.awsapps.com/start/#
2. Click on AWS Account 309820967897
3. Copy credentials

Set environment variables:

**Windows:**
```cmd
set AWS_ACCESS_KEY_ID=ASIA...
set AWS_SECRET_ACCESS_KEY=...
set AWS_SESSION_TOKEN=...
set REDSHIFT_PASSWORD=<your-password>
set SSH_PASSWORD=<your-ssh-password>
```

**Linux/Mac:**
```bash
export AWS_ACCESS_KEY_ID=ASIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
export REDSHIFT_PASSWORD=<your-password>
export SSH_PASSWORD=<your-ssh-password>
```

### 1.3 Verify Credentials

```bash
python setup_credentials.py
```

Choose option 3 to check credentials. Expected output:
```
✅ Credentials valid
   Account: 309820967897
   User: arn:aws:sts::309820967897:assumed-role/...
```

## Phase 2: AWS Infrastructure Deployment

### 2.1 Deploy Infrastructure

```bash
python deploy_infrastructure.py
```

This will create:

1. **S3 Buckets**
   - meraki-webhooks-raw-309820967897 (raw payload storage)
   - meraki-webhooks-backup-309820967897 (Firehose backup)

2. **IAM Roles**
   - MerakiLambdaRole (Lambda execution)
   - MerakiFirehoseRole (Firehose delivery)

3. **Lambda Function**
   - Name: meraki-webhook-processor
   - Runtime: Python 3.9
   - Memory: 512 MB
   - Timeout: 60 seconds

4. **API Gateway**
   - Name: meraki-webhook-api
   - Stage: prod
   - Endpoint: /webhook

5. **Kinesis Firehose**
   - Name: meraki-redshift-stream
   - Destination: S3 (backup)
   - Buffer: 5 MB or 300 seconds

Expected output:
```
============================================================
Deploying Meraki Webhook Streaming Infrastructure
============================================================

1. Creating S3 buckets...
✅ S3 bucket exists: meraki-webhooks-raw-309820967897
✅ S3 bucket exists: meraki-webhooks-backup-309820967897

2. Creating IAM roles...
✅ Created IAM role: MerakiLambdaRole
  ✅ Attached policy: LambdaBasicExecution
  ✅ Attached policy: FirehoseAccess
  ✅ Attached policy: S3Access
✅ Created IAM role: MerakiFirehoseRole
  ✅ Attached policy: FirehoseS3Access
  ✅ Attached policy: FirehoseLogsAccess

3. Creating Lambda function...
✅ Created Lambda function: meraki-webhook-processor

4. Creating API Gateway...
✅ Created API Gateway: meraki-webhook-api
✅ API Gateway URL: https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/webhook

5. Creating Firehose stream...
✅ Created Firehose stream: meraki-redshift-stream

============================================================
✅ Deployment Complete!
============================================================

Webhook URL: https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/webhook
Raw Storage: s3://meraki-webhooks-raw-309820967897/raw/
Backup Storage: s3://meraki-webhooks-backup-309820967897/firehose-backup/

Deployment info saved to: deployment_info.json
```

### 2.2 Save Webhook URL

Copy the webhook URL from the output. You'll need this for Meraki configuration.

## Phase 3: Redshift Schema Setup

### 3.1 Establish SSH Tunnel

Open a separate terminal and establish SSH tunnel:

```bash
ssh -L 5439:edna-prod-dw.cejfjblsis8x.us-east-1.redshift.amazonaws.com:5439 chris.cestari@44.207.39.121
```

Keep this terminal open during schema setup.

### 3.2 Create Redshift Schema

In your main terminal:

```bash
python setup_redshift_schema.py
```

This will:
1. Connect to Redshift via SSH tunnel
2. Create schema: edna_stream_meraki
3. Create table: meraki_webhooks
4. Create views: recent_alerts, temperature_alerts
5. Grant permissions

Expected output:
```
Setting up Redshift schema for Meraki webhooks...
Establishing SSH tunnel...
✅ SSH tunnel established

Creating schema: edna_stream_meraki
✅ Schema created: edna_stream_meraki

Creating meraki_webhooks table...
✅ Table created: edna_stream_meraki.meraki_webhooks

Creating convenience views...
✅ View created: edna_stream_meraki.recent_alerts
✅ View created: edna_stream_meraki.temperature_alerts

Granting permissions...
✅ Permissions granted

============================================================
✅ Redshift schema setup complete!
============================================================

Schema: edna_stream_meraki
Table: edna_stream_meraki.meraki_webhooks
Views: edna_stream_meraki.recent_alerts, edna_stream_meraki.temperature_alerts
```

## Phase 4: Testing

### 4.1 Test Webhook Endpoint

```bash
python test_webhook.py
```

Expected output:
```
============================================================
Testing Meraki Webhook Endpoint
============================================================

URL: https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/webhook
Tests: 1

[1/1] Sending webhook...
✅ Success: 200
   Response: {'status': 'success', 'message': 'Webhook received and processed', 'request_id': '...'}

============================================================
Test Summary
============================================================
Total: 1
✅ Success: 1
❌ Failed: 0
```

### 4.2 Verify Data in S3

Check raw storage:
```bash
aws s3 ls s3://meraki-webhooks-raw-309820967897/raw/
```

### 4.3 Verify Data in Redshift

Connect to Redshift and query:

```sql
SELECT * FROM edna_stream_meraki.meraki_webhooks 
ORDER BY ingestion_timestamp DESC 
LIMIT 5;
```

## Phase 5: Meraki Configuration

### 5.1 Add Webhook Receiver

1. Log into Meraki Dashboard
2. Go to **Network-wide** → **Alerts**
3. Scroll to **Webhooks**
4. Click **Add an HTTP server**

Configuration:
- **Name**: AWS Redshift Webhook
- **URL**: (paste your API Gateway URL)
- **Shared secret**: (optional, for validation)

### 5.2 Configure Alert Types

Select which alerts to send:
- ✅ Sensor alerts (temperature, humidity, water, door)
- ✅ Motion alerts
- ✅ Device status alerts
- ✅ Network alerts

### 5.3 Test from Meraki

1. Click **Send test webhook**
2. Verify in CloudWatch Logs
3. Check Redshift for new record

## Phase 6: Monitoring Setup

### 6.1 CloudWatch Logs

Monitor Lambda execution:
```
Log Group: /aws/lambda/meraki-webhook-processor
```

Monitor Firehose delivery:
```
Log Group: /aws/kinesisfirehose/meraki-redshift-stream
```

### 6.2 Create CloudWatch Alarms (Optional)

```bash
# Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name meraki-webhook-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=meraki-webhook-processor
```

## Phase 7: Credential Rotation

AWS credentials expire every 30 minutes. When they expire:

### 7.1 Get New Credentials

1. Visit AWS SSO: https://d-9067640efb.awsapps.com/start/#
2. Copy new credentials

### 7.2 Update Environment

```bash
set AWS_ACCESS_KEY_ID=<new-key>
set AWS_SECRET_ACCESS_KEY=<new-secret>
set AWS_SESSION_TOKEN=<new-token>
```

### 7.3 Refresh Credentials

```bash
python setup_credentials.py
```

Choose option 4 to refresh from environment.

## Troubleshooting

### Issue: Credentials Invalid

**Symptom:**
```
❌ Credentials invalid: An error occurred (ExpiredToken)
```

**Solution:**
Get fresh credentials from AWS SSO and refresh.

### Issue: Lambda Timeout

**Symptom:**
```
Task timed out after 60.00 seconds
```

**Solution:**
Increase timeout in config.json:
```json
{
  "lambda": {
    "timeout_seconds": 120
  }
}
```

Then redeploy Lambda.

### Issue: No Data in Redshift

**Symptom:**
No records in meraki_webhooks table.

**Solution:**
1. Check Lambda logs for errors
2. Verify Firehose is delivering to S3
3. Check S3 backup bucket for files
4. Verify Redshift COPY command permissions

### Issue: SSH Tunnel Fails

**Symptom:**
```
Connection refused
```

**Solution:**
1. Verify SSH key permissions: `chmod 600 ssh/edna-prod-bastion-host-key-pair.pem`
2. Test SSH connection: `ssh chris.cestari@44.207.39.121`
3. Verify bastion host is running

### Issue: API Gateway 403 Error

**Symptom:**
```
{"message":"Missing Authentication Token"}
```

**Solution:**
Verify you're using the correct URL with /webhook path.

## Verification Checklist

- [ ] AWS credentials valid
- [ ] S3 buckets created
- [ ] IAM roles created
- [ ] Lambda function deployed
- [ ] API Gateway created
- [ ] Firehose stream created
- [ ] Redshift schema created
- [ ] Test webhook successful
- [ ] Data in S3 raw storage
- [ ] Data in Redshift table
- [ ] Meraki webhook configured
- [ ] CloudWatch logs accessible

## Next Steps

1. **Load Historical Data**
   - Use load_historical_data.py to import existing webhooks from s3://edna-dev-meraki-webhooks/

2. **Create Analytics Views**
   - Build Redshift views for common queries
   - Create dashboards in your BI tool

3. **Setup Alerts**
   - Configure CloudWatch alarms for failures
   - Set up SNS notifications

4. **Document Meraki Configuration**
   - Document which alert types are enabled
   - Document webhook configuration

5. **Schedule Maintenance**
   - Set reminders for credential rotation
   - Plan for Lambda function updates

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review this deployment guide
3. Check README.md for common issues
4. Verify all prerequisites are met

---

**Deployment complete!** Your Meraki webhooks are now streaming to Redshift.
