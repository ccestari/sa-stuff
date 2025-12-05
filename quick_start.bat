@echo off
REM Quick Start Script for Meraki Webhook Streaming
REM Runs all deployment steps in sequence

echo ============================================================
echo Meraki Webhook Streaming - Quick Start
echo ============================================================
echo.
echo This script will:
echo   1. Check AWS credentials
echo   2. Deploy AWS infrastructure
echo   3. Setup Redshift schema
echo   4. Test webhook endpoint
echo.
echo Make sure you have:
echo   - Set AWS credentials (run init_credentials.bat first)
echo   - Redshift password ready
echo   - SSH password ready
echo.
pause

echo.
echo ============================================================
echo Step 1: Checking AWS Credentials
echo ============================================================
python setup_credentials.py
if errorlevel 1 (
    echo.
    echo ERROR: Credentials check failed
    echo Please run init_credentials.bat first
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 2: Deploying AWS Infrastructure
echo ============================================================
python deploy_infrastructure.py
if errorlevel 1 (
    echo.
    echo ERROR: Infrastructure deployment failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 3: Setting up Redshift Schema
echo ============================================================
echo.
echo NOTE: You will need to provide:
echo   - Redshift password
echo   - SSH password
echo.
python setup_redshift_schema.py
if errorlevel 1 (
    echo.
    echo ERROR: Redshift schema setup failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 4: Testing Webhook Endpoint
echo ============================================================
python test_webhook.py
if errorlevel 1 (
    echo.
    echo ERROR: Webhook test failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Quick Start Complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Configure Meraki Dashboard with webhook URL
echo   2. Monitor CloudWatch logs
echo   3. Query Redshift for data
echo   4. (Optional) Load historical data: python load_historical_data.py
echo.
echo Webhook URL is in deployment_info.json
echo.
pause
