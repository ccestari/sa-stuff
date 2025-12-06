#!/bin/bash
# macOS/Linux version of sync script
# Runs sync_s3_to_redshift.py every 5 minutes

echo "=========================================="
echo "Meraki S3 → Redshift Sync (macOS/Linux)"
echo "=========================================="
echo "Press Ctrl+C to stop"
echo ""

while true; do
    python3 sync_s3_to_redshift.py
    sleep 300
done
