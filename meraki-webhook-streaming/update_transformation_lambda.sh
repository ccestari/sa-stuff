#!/bin/bash

# Create deployment package
echo "Creating deployment package..."
zip -j transformation_lambda.zip fixed_transformation_lambda.py

# Update the Lambda function
echo "Updating Lambda function..."
aws lambda update-function-code \
    --function-name firehose-data-transformation \
    --zip-file fileb://transformation_lambda.zip

# Wait for update to complete
echo "Waiting for update to complete..."
aws lambda wait function-updated --function-name firehose-data-transformation

echo "Lambda function updated successfully!"

# Clean up
rm transformation_lambda.zip

echo "Test the webhook again - the transformation should now work."