#!/bin/bash

echo "=== AWS Credential Status ==="
aws sts get-caller-identity 2>&1

if [ $? -ne 0 ]; then
  echo -e "\n❌ AWS credentials are expired or not configured"
  echo -e "\nPlease authenticate using ONE of these methods:\n"
  echo "1. AWS SSO:"
  echo "   aws sso login --profile <your-profile>"
  echo ""
  echo "2. Set environment variables:"
  echo "   export AWS_ACCESS_KEY_ID=<key>"
  echo "   export AWS_SECRET_ACCESS_KEY=<secret>"
  echo "   export AWS_SESSION_TOKEN=<token>  # if using temporary credentials"
  echo ""
  echo "3. AWS CLI configure:"
  echo "   aws configure"
  echo ""
  echo "Then run this script again."
  exit 1
fi

echo -e "\n✅ Credentials valid. Running diagnostics...\n"
./debug_pipeline.sh
