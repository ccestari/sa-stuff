#!/bin/bash
# Continuous S3 to Redshift sync for Meraki webhooks
# Runs every 5 minutes without VPN/SSH requirements

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Meraki Webhook Continuous Sync"
echo "Started: $(date)"
echo "=========================================="
echo ""

while true; do
    echo "[$(date)] Starting sync cycle..."
    
    # Check S3 data
    echo "  → Checking S3 for new webhooks..."
    python3 check_s3_data.py 2>&1 | tee /tmp/s3_output.log
    
    # Check for expired credentials
    if grep -q "ExpiredToken\|ExpiredTokenException" /tmp/s3_output.log; then
        echo ""
        echo "⚠️  AWS credentials expired!"
        echo "Run: python3 update_credentials.py"
        echo "Then restart this script."
        exit 1
    fi
    
    # Check Lambda logs
    echo "  → Checking Lambda logs..."
    python3 check_lambda_logs.py 2>&1 | tee /tmp/lambda_output.log
    
    # Check for expired credentials
    if grep -q "ExpiredToken\|ExpiredTokenException" /tmp/lambda_output.log; then
        echo ""
        echo "⚠️  AWS credentials expired!"
        echo "Run: python3 update_credentials.py"
        echo "Then restart this script."
        exit 1
    fi
    
    echo "[$(date)] ✅ Sync cycle complete"
    echo "  → Waiting 5 minutes..."
    echo ""
    
    sleep 300  # 5 minutes
done
