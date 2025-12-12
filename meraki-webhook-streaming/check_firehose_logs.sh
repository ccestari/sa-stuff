#!/bin/bash

echo "=== Firehose CloudWatch Log Streams ==="
aws logs describe-log-streams \
  --log-group-name /aws/kinesisfirehose/meraki-firehose \
  --order-by LastEventTime \
  --descending \
  --max-items 5 \
  --region us-east-1

echo -e "\n=== Recent Firehose Destination Delivery Logs ==="
aws logs tail /aws/kinesisfirehose/meraki-firehose --since 24h --filter-pattern "DestinationDelivery" --region us-east-1 --format short 2>/dev/null || echo "No logs found"

echo -e "\n=== Recent Firehose Backup Delivery Logs ==="
aws logs tail /aws/kinesisfirehose/meraki-firehose --since 24h --filter-pattern "BackupDelivery" --region us-east-1 --format short 2>/dev/null || echo "No logs found"

echo -e "\n=== Firehose Error Logs ==="
aws logs tail /aws/kinesisfirehose/meraki-firehose --since 24h --filter-pattern "ERROR" --region us-east-1 --format short 2>/dev/null || echo "No errors found"

echo -e "\n=== Check S3 Backup Bucket for Failed Records ==="
aws s3 ls s3://edna-meraki-firehose-backup/ --recursive --human-readable --summarize
