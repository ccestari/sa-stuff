#!/bin/bash

# Check IAM permissions for the pipeline components

echo "=== Lambda Execution Role (Webhook Handler) ==="
LAMBDA_ROLE=$(aws lambda get-function --function-name edna-meraki-iceberg-load-from-webhook --region us-east-1 --query 'Configuration.Role' --output text)
echo "Role ARN: $LAMBDA_ROLE"
LAMBDA_ROLE_NAME=$(echo $LAMBDA_ROLE | awk -F'/' '{print $NF}')
aws iam get-role --role-name $LAMBDA_ROLE_NAME

echo -e "\n=== Lambda Attached Policies ==="
aws iam list-attached-role-policies --role-name $LAMBDA_ROLE_NAME

echo -e "\n=== Firehose Execution Role ==="
FIREHOSE_ROLE=$(aws firehose describe-delivery-stream --delivery-stream-name meraki-firehose --region us-east-1 --query 'DeliveryStreamDescription.Destinations[0].IcebergDestinationDescription.RoleARN' --output text)
echo "Role ARN: $FIREHOSE_ROLE"
FIREHOSE_ROLE_NAME=$(echo $FIREHOSE_ROLE | awk -F'/' '{print $NF}')
aws iam list-attached-role-policies --role-name $FIREHOSE_ROLE_NAME

echo -e "\n=== Transformation Lambda Role ==="
TRANSFORM_ROLE=$(aws lambda get-function --function-name firehose-data-transformation --region us-east-1 --query 'Configuration.Role' --output text)
echo "Role ARN: $TRANSFORM_ROLE"
TRANSFORM_ROLE_NAME=$(echo $TRANSFORM_ROLE | awk -F'/' '{print $NF}')
aws iam list-attached-role-policies --role-name $TRANSFORM_ROLE_NAME
