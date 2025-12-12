@echo off
REM Initialize AWS credentials for Meraki Webhook Streaming
REM Update these values with your current AWS SSO credentials

echo ============================================================
echo Meraki Webhook Streaming - Credential Initialization
echo ============================================================
echo.
echo IMPORTANT: AWS credentials expire every 30 minutes
echo Get fresh credentials from: https://d-9067640efb.awsapps.com/start/#
echo.

REM Set AWS credentials (UPDATE THESE VALUES)
set AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_HERE
set AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY_HERE
set AWS_SESSION_TOKEN=YOUR_SESSION_TOKEN_HERE

REM Set Redshift and SSH passwords
set REDSHIFT_PASSWORD=YOUR_REDSHIFT_PASSWORD
set SSH_PASSWORD=YOUR_SSH_PASSWORD

echo Credentials set for this session.
echo.
echo Next steps:
echo   1. python deploy_infrastructure.py
echo   2. python setup_redshift_schema.py
echo   3. python test_webhook.py
echo.
echo Remember to refresh credentials when they expire!
echo ============================================================
