#!/usr/bin/env python3
"""
Deploy webhook streaming infrastructure
Creates Lambda with sa_utils bundled, API Gateway, S3, and Firehose
"""
import json
import boto3
import zipfile
import io
import os
import shutil
from pathlib import Path


def package_lambda_with_sa_utils(sa_utils_path='../../sa-utils'):
    """Package Lambda function with sa_utils included"""
    print("Creating Lambda deployment package...")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add lambda function
        zf.write('lambda_function.py', 'lambda_function.py')
        
        # Add sa_utils
        sa_utils_dir = Path(sa_utils_path).resolve()
        for root, dirs, files in os.walk(sa_utils_dir):
            # Skip __pycache__ and other unnecessary dirs
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'unit_tests']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    arcname = str(file_path.relative_to(sa_utils_dir.parent))
                    zf.write(file_path, arcname)
    
    zip_buffer.seek(0)
    print(f"✅ Package created ({len(zip_buffer.getvalue())} bytes)")
    return zip_buffer.read()


def create_lambda(config, zip_content):
    """Create or update Lambda function"""
    lambda_client = boto3.client('lambda', region_name=config['aws']['region'])
    function_name = config['lambda']['function_name']
    
    # Create IAM role first (simplified - should use existing or create properly)
    role_arn = f"arn:aws:iam::{config['aws']['account_id']}:role/{function_name}-role"
    
    try:
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime=config['lambda']['runtime'],
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=config['lambda']['timeout_seconds'],
            MemorySize=config['lambda']['memory_mb'],
            Environment={
                'Variables': {
                    'WEBHOOK_SOURCE': function_name,
                    'ENVIRONMENT': 'production',
                    'RAW_BUCKET': config['s3']['raw_bucket'],
                    'FIREHOSE_STREAM': config['firehose']['stream_name']
                }
            }
        )
        print(f"✅ Created Lambda: {function_name}")
        return response['FunctionArn']
    except lambda_client.exceptions.ResourceConflictException:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"✅ Updated Lambda: {function_name}")
        return response['FunctionArn']


def create_s3_buckets(config):
    """Create S3 buckets"""
    s3 = boto3.client('s3', region_name=config['aws']['region'])
    
    for bucket in [config['s3']['raw_bucket'], config['s3']['backup_bucket']]:
        try:
            s3.head_bucket(Bucket=bucket)
            print(f"✅ S3 bucket exists: {bucket}")
        except:
            s3.create_bucket(Bucket=bucket)
            print(f"✅ Created S3 bucket: {bucket}")


def create_api_gateway(config, lambda_arn):
    """Create API Gateway"""
    apigw = boto3.client('apigateway', region_name=config['aws']['region'])
    lambda_client = boto3.client('lambda', region_name=config['aws']['region'])
    
    # Create REST API
    api = apigw.create_rest_api(
        name=config['api_gateway']['api_name'],
        endpointConfiguration={'types': ['REGIONAL']}
    )
    api_id = api['id']
    
    # Get root resource
    resources = apigw.get_resources(restApiId=api_id)
    root_id = resources['items'][0]['id']
    
    # Create /webhook resource
    resource = apigw.create_resource(
        restApiId=api_id,
        parentId=root_id,
        pathPart='webhook'
    )
    
    # Create POST method
    apigw.put_method(
        restApiId=api_id,
        resourceId=resource['id'],
        httpMethod='POST',
        authorizationType='NONE'
    )
    
    # Set Lambda integration
    apigw.put_integration(
        restApiId=api_id,
        resourceId=resource['id'],
        httpMethod='POST',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=f"arn:aws:apigateway:{config['aws']['region']}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    )
    
    # Deploy
    apigw.create_deployment(
        restApiId=api_id,
        stageName=config['api_gateway']['stage_name']
    )
    
    # Add Lambda permission
    lambda_client.add_permission(
        FunctionName=config['lambda']['function_name'],
        StatementId='apigateway-invoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f"arn:aws:execute-api:{config['aws']['region']}:{config['aws']['account_id']}:{api_id}/*/*"
    )
    
    url = f"https://{api_id}.execute-api.{config['aws']['region']}.amazonaws.com/{config['api_gateway']['stage_name']}/webhook"
    print(f"✅ Created API Gateway: {url}")
    return url


def main():
    with open('config.json') as f:
        config = json.load(f)
    
    print("=" * 60)
    print("Deploying Webhook Streaming Infrastructure")
    print("=" * 60)
    
    # Package Lambda with sa_utils
    zip_content = package_lambda_with_sa_utils()
    
    # Create S3 buckets
    print("\n1. Creating S3 buckets...")
    create_s3_buckets(config)
    
    # Create Lambda
    print("\n2. Creating Lambda function...")
    lambda_arn = create_lambda(config, zip_content)
    
    # Create API Gateway
    print("\n3. Creating API Gateway...")
    api_url = create_api_gateway(config, lambda_arn)
    
    # Save deployment info
    deployment_info = {
        'api_url': api_url,
        'lambda_arn': lambda_arn,
        'raw_bucket': config['s3']['raw_bucket']
    }
    
    with open('deployment_info.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Deployment Complete!")
    print("=" * 60)
    print(f"\nWebhook URL: {api_url}")
    print(f"Test with: python test_webhook.py --url {api_url}")


if __name__ == "__main__":
    main()
