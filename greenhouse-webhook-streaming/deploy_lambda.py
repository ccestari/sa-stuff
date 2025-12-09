"""
Deploy Lambda function
Utility for updating Lambda code
"""
import boto3
import zipfile
import os
import json

def create_deployment_package(source_file='lambda_function.py'):
    """Create Lambda deployment zip"""
    
    zip_path = 'lambda_deployment.zip'
    
    print(f"Creating deployment package from {source_file}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(source_file, 'lambda_function.py')
    
    size = os.path.getsize(zip_path)
    print(f"[OK] Created {zip_path} ({size} bytes)")
    
    return zip_path

def deploy_lambda(function_name, zip_path):
    """Deploy Lambda function to AWS"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    print(f"\nDeploying to Lambda function: {function_name}")
    
    try:
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content,
            Publish=True
        )
        
        print(f"[OK] Deployed successfully")
        print(f"[OK] Version: {response['Version']}")
        print(f"[OK] Last Modified: {response['LastModified']}")
        print(f"[OK] Code Size: {response['CodeSize']} bytes")
        print(f"[OK] Runtime: {response['Runtime']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}")
        return False

def get_lambda_info(function_name):
    """Get Lambda function information"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        
        config = response['Configuration']
        print(f"\nLambda Function: {function_name}")
        print(f"  Runtime: {config['Runtime']}")
        print(f"  Memory: {config['MemorySize']} MB")
        print(f"  Timeout: {config['Timeout']} seconds")
        print(f"  Last Modified: {config['LastModified']}")
        print(f"  Role: {config['Role']}")
        
        if 'Environment' in config:
            print(f"  Environment Variables:")
            for key, value in config['Environment'].get('Variables', {}).items():
                print(f"    {key}: {value}")
        
        return config
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

if __name__ == '__main__':
    function_name = 'greenhouse-webhook-processor'
    
    # Show current info
    print("Current Lambda configuration:")
    get_lambda_info(function_name)
    
    # Create and deploy
    print("\n" + "=" * 80)
    zip_path = create_deployment_package()
    
    if deploy_lambda(function_name, zip_path):
        print("\n[SUCCESS] Deployment complete!")
    else:
        print("\n[FAILED] Deployment failed")
    
    # Cleanup
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print(f"[OK] Cleaned up {zip_path}")
