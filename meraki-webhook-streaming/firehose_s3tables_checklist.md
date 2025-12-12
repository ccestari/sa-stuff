# AWS Firehose S3 Tables Delivery Troubleshooting Checklist

## Issue: Firehose delivers to S3 backup but not to S3 Tables (Iceberg)

### 1. Firehose Configuration Check
**AWS Console: Kinesis Data Firehose > meraki-firehose**

- [ ] **Destination Type**: Verify it's set to "Apache Iceberg tables in Amazon S3"
- [ ] **Catalog Configuration**: 
  - Catalog ARN: `arn:aws:glue:us-east-1:309820967897:catalog/s3tablescatalog/lakehouse-meraki`
  - Database: `s3tablescatalog`
  - Table: `lakehouse-meraki`
- [ ] **S3 Tables Bucket**: `arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki`

### 2. IAM Role Permissions
**Check the Firehose service role has these permissions:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3tables:PutObject",
                "s3tables:GetObject",
                "s3tables:GetBucket"
            ],
            "Resource": [
                "arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki",
                "arn:aws:s3tables:us-east-1:309820967897:bucket/lakehouse-meraki/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "glue:GetTable",
                "glue:GetDatabase",
                "glue:GetPartitions",
                "glue:UpdateTable"
            ],
            "Resource": [
                "arn:aws:glue:us-east-1:309820967897:catalog",
                "arn:aws:glue:us-east-1:309820967897:database/s3tablescatalog",
                "arn:aws:glue:us-east-1:309820967897:table/s3tablescatalog/lakehouse-meraki"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": "arn:aws:lambda:us-east-1:309820967897:function:firehose-data-transformation"
        }
    ]
}
```

### 3. S3 Tables Bucket Check
**AWS Console: S3 Tables > lakehouse-meraki**

- [ ] **Bucket exists and is active**
- [ ] **Bucket policy allows Firehose access**
- [ ] **Check bucket region** (must be us-east-1)

### 4. Glue Catalog Table Check
**AWS Console: Glue > Data Catalog > Tables**

- [ ] **Database `s3tablescatalog` exists**
- [ ] **Table `lakehouse-meraki` exists**
- [ ] **Table format is Iceberg**
- [ ] **Table location points to S3 Tables bucket**
- [ ] **Schema matches your data structure**

### 5. Lambda Function Check
**AWS Console: Lambda > firehose-data-transformation**

- [ ] **Function executes successfully**
- [ ] **Resource policy allows Firehose to invoke**
- [ ] **Output format matches Iceberg requirements**

### 6. Common Issues & Solutions

#### Issue: Table Schema Mismatch
- **Check**: Lambda output schema matches Glue table schema
- **Fix**: Update Glue table schema or modify Lambda transformation

#### Issue: Missing S3 Tables Permissions
- **Check**: Firehose role has `s3tables:*` permissions
- **Fix**: Add S3 Tables permissions to Firehose service role

#### Issue: Incorrect Catalog Configuration
- **Check**: Catalog ARN format and table exists
- **Fix**: Verify Glue catalog database and table names

#### Issue: Data Format Problems
- **Check**: Lambda outputs valid Parquet/Iceberg format
- **Fix**: Ensure Lambda returns properly formatted records

### 7. Monitoring & Debugging

**CloudWatch Logs to Check:**
- `/aws/kinesisfirehose/meraki-firehose`
- `/aws/lambda/firehose-data-transformation`

**CloudWatch Metrics to Monitor:**
- `DeliveryToS3Tables.Records`
- `DeliveryToS3Tables.Success`
- `DeliveryToS3Tables.DataFreshness`

**Key Error Patterns:**
- "AccessDenied" → IAM permissions issue
- "NoSuchTable" → Glue catalog configuration
- "SchemaEvolutionException" → Schema mismatch
- "InvalidRecordFormat" → Lambda transformation issue

### 8. Quick Fixes to Try

1. **Restart Firehose**: Stop and start the delivery stream
2. **Check Error Logs**: Look for specific error messages in CloudWatch
3. **Test Lambda**: Manually invoke with sample Firehose payload
4. **Verify Schema**: Ensure data matches table schema exactly