# AWS Utilities

Reusable AWS utilities for SA data engineering projects.

## Modules

### credential_manager.py

Manages AWS credentials with validation and refresh capabilities.

**Usage:**

```python
from credential_manager import CredentialManager

# Initialize
cred_mgr = CredentialManager('credentials.yaml')

# Ensure credentials are valid (prompts if expired)
cred_mgr.ensure_valid_credentials()

# Get boto3 session
session = cred_mgr.get_session()
client = session.client('s3')
```

### cloudwatch_utils.py

CloudWatch metrics utilities.

**Functions:**
- `get_lambda_metrics(function_name, hours=1)` - Get Lambda invocation/error metrics

### firehose_utils.py

Firehose monitoring and management utilities.

**Functions:**
- `check_firehose_metrics(stream_name, hours=1)` - Monitor Firehose delivery
- `add_firehose_permissions_to_lambda(role_name, firehose_arn)` - Add IAM permissions

## Credentials Setup

1. Copy template:
   ```bash
   cp credentials.yaml.template credentials.yaml
   ```

2. Fill in your AWS credentials (rotate every 30 minutes)

3. Never commit credentials.yaml (already in .gitignore)
