#!/bin/bash
# Setup cron job on EC2 bastion to run sync every 5 minutes

# Install dependencies
pip3 install psycopg2-binary boto3

# Create cron job
(crontab -l 2>/dev/null; echo "*/5 * * * * cd /home/ec2-user/meraki-webhook-streaming && /usr/bin/python3 ec2_sync_redshift.py >> /var/log/meraki-sync.log 2>&1") | crontab -

echo "✅ Cron job installed - runs every 5 minutes"
echo "View logs: tail -f /var/log/meraki-sync.log"
