# SA-Utils

Shared utilities for Success Academy data engineering projects.

## Structure

```
sa-utils/
├── webhook-utils/     # Generic webhook streaming utilities
│   ├── check_s3_data.py
│   ├── check_lambda_logs.py
│   ├── test_webhook.py
│   ├── update_lambda.py
│   ├── invoke_lambda_directly.py
│   ├── fix_api_gateway.py
│   └── README.md
└── README.md
```

## Webhook Utilities

Generic scripts for managing webhook streaming projects (Meraki, Greenhouse, etc.)

See [webhook-utils/README.md](webhook-utils/README.md) for detailed documentation.

### Quick Start

```bash
cd /path/to/your-webhook-project

# Check S3 data
python3 ../sa-utils/webhook-utils/check_s3_data.py

# Check Lambda logs
python3 ../sa-utils/webhook-utils/check_lambda_logs.py

# Test webhook endpoint
python3 ../sa-utils/webhook-utils/test_webhook.py --url YOUR_API_GATEWAY_URL

# Update Lambda code
python3 ../sa-utils/webhook-utils/update_lambda.py
```

## Requirements

```bash
pip install boto3 pyyaml requests
```

## Configuration

All webhook utilities expect:
- `config.json` - Project configuration
- `credentials.yaml` - AWS credentials

## Adding New Utilities

When creating new utilities:
1. Make them generic and reusable across projects
2. Use command-line arguments for project-specific values
3. Default to reading from `config.json` and `credentials.yaml`
4. Include clear documentation and examples
