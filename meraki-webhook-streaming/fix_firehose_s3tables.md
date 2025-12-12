# URGENT: Firehose S3 Tables Configuration Fixes

## Root Cause
Your Firehose is configured for Iceberg delivery but has **NO destination table configured** and the Glue catalog doesn't exist.

## Required Fixes (In Order):

### 1. Create Glue Database
```bash
aws glue create-database \
  --catalog-id 309820967897 \
  --database-input Name=s3tablescatalog,Description="S3 Tables catalog for Iceberg tables" \
  --region us-east-1
```

### 2. Create S3 Tables Bucket (if not exists)
```bash
aws s3tables create-table-bucket \
  --name lakehouse-meraki \
  --region us-east-1
```

### 3. Create Iceberg Table in Glue Catalog
```bash
aws glue create-table \
  --catalog-id 309820967897 \
  --database-name s3tablescatalog \
  --table-input '{
    "Name": "lakehouse-meraki",
    "StorageDescriptor": {
      "Columns": [
        {"Name": "timestamp", "Type": "timestamp"},
        {"Name": "data", "Type": "string"}
      ],
      "Location": "s3://lakehouse-meraki/",
      "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
      "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
      "SerdeInfo": {
        "SerializationLibrary": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
      }
    },
    "Parameters": {
      "table_type": "ICEBERG",
      "metadata_location": "s3://lakehouse-meraki/metadata/"
    }
  }' \
  --region us-east-1
```

### 4. Update Firehose Configuration
**AWS Console: Kinesis Data Firehose > meraki-firehose > Configuration**

1. **Edit Destination**
2. **Add Destination Table Configuration:**
   - Table Name: `lakehouse-meraki`
   - Database: `s3tablescatalog`
   - S3 Tables Bucket ARN: `arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki`

3. **Enable Schema Evolution** (recommended)
4. **Enable Table Creation** (recommended)
5. **Change S3 Backup Mode** to "AllData" for troubleshooting

### 5. Update IAM Role Permissions
Add these permissions to role `EdnaFirehoseToS3Iceberg`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3tables:PutObject",
                "s3tables:GetObject",
                "s3tables:GetBucket",
                "s3tables:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki",
                "arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki/*"
            ]
        }
    ]
}
```

## Why It's Not Working:
- **DestinationTableConfigurationList is EMPTY** - Firehose has no table to deliver to
- **Glue catalog doesn't exist** - Can't validate schema or table structure
- **No S3 Tables permissions** - IAM role likely missing S3 Tables access

## Quick Test:
After fixes, send test data:
```bash
aws firehose put-record \
  --delivery-stream-name meraki-firehose \
  --record Data='{"timestamp":"2024-01-01T00:00:00Z","message":"test"}' \
  --region us-east-1
```