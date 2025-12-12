@echo off
REM Run complete analysis and setup workflow

echo ============================================================
echo Meraki Webhook Streaming - Analysis and Setup
echo ============================================================
echo.
echo This will:
echo   1. Analyze historical data for schema variations
echo   2. Copy historical data to production
echo   3. Setup Redshift schema in db02
echo.
pause

echo.
echo Step 1: Analyzing historical data...
python analyze_historical_data.py
if errorlevel 1 (
    echo ERROR: Analysis failed
    pause
    exit /b 1
)

echo.
echo Step 2: Copying historical data to production...
python copy_historical_data.py
if errorlevel 1 (
    echo ERROR: Copy failed
    pause
    exit /b 1
)

echo.
echo Step 3: Setting up Redshift schema...
python setup_redshift_schema.py
if errorlevel 1 (
    echo ERROR: Schema setup failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Complete!
echo ============================================================
pause
