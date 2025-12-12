#!/bin/bash

echo "Setting up Firehose S3 Tables configuration..."

echo "1. Creating Glue table..."
aws glue create-table --catalog-id 309820967897 --database-name s3tablescatalog --table-input '{
  "Name": "lakehouse-meraki",
  "StorageDescriptor": {
    "Columns": [
      {"Name": "timestamp", "Type": "timestamp"},
      {"Name": "network_id", "Type": "string"},
      {"Name": "device_serial", "Type": "string"},
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
    "classification": "iceberg"
  }
}' --region us-east-1

echo "2. Adding S3 Tables permissions to IAM role..."
aws iam put-role-policy --role-name EdnaFirehoseToS3Iceberg --policy-name S3TablesAccess --policy-document '{
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
}' --region us-east-1

echo "Setup complete!"