#!/usr/bin/env python3
"""
Deploy AWS infrastructure for Meraki webhook streaming
Creates: IAM roles, Lambda, API Gateway, Kinesis Firehose, S3 buckets
"""
import json
import boto3
import zipfile
import io
import time
from botocore.exceptions import ClientError
from setup_credentials import CredentialManager

class InfrastructureDeployer:
    def __init__(self, config_file='config.json'):
        with open(config_file) as f:
            self.config = json.load(f)
        
        # Initialize credential manager
        self.cred_manager = CredentialManager()
        if not self.cred_manager.load_credentials() or not self.cred_manager.are_credentials_valid():
            raise Exception("AWS credentials not valid. Run: python setup_credentials.py")
        
        # Get boto3 session
        session = self.cred_manager.get_boto3_session()
        self.iam = session.client('iam')
        self.lambda_client = session.client('lambda')
        self.apigateway = session.client('apigateway')
        self.firehose = session.client('firehose')
        self.s3 = session.client('s3')
        
        self.deployment_info = {}
    
    def create_s3_buckets(self):
        """Create S3 buckets for raw storage and backup"""
        buckets = [
            self.config['s3']['raw_bucket'],
            self.config['s3']['backup_bucket']
        ]
        
        for bucket_name in buckets:
            try:
                self.s3.head_bucket(Bucket=bucket_name)
                print(f"✅ S3 bucket exists: {bucket_name}")
            except ClientError:
                try:
                    self.s3.create_bucket(Bucket=bucket_name)
                    print(f"✅ Created S3 bucket: {bucket_name}")
                except ClientError as e:
                    print(f"❌ Error creating S3 bucket {bucket_name}: {e}")
    
    def create_iam_role(self, role_name, assume_role_policy, policies):
        """Create IAM role with policies"""
        try:
            # Create role
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description=f'Role for {role_name}'
            )
            role_arn = response['Role']['Arn']
            print(f"✅ Created IAM role: {role_name}")
            
            # Attach policies
            for policy_name, policy_doc in policies.items():
                self.iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_doc)
                )
                print(f"  ✅ Attached policy: {policy_name}")
            
            # Wait for role to propagate
            time.sleep(10)
            
            return role_arn
            
        except ClientError as e:
            if 'EntityAlreadyExists' in str(e):
                response = self.iam.get_role(RoleName=role_name)
                print(f"ℹ️  IAM role already exists: {role_name}")
                return response['Role']['Arn']
            else:
                print(f"❌ Error creating IAM role: {e}")
                return None
    
    def create_lambda_role(self):
        """Create IAM role for Lambda"""
        role_name = self.config['iam']['lambda_role_name']
        
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        policies = {
            "LambdaBasicExecution": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }]
            },
            "FirehoseAccess": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "firehose:PutRecord",
                        "firehose:PutRecordBatch"
                    ],
                    "Resource": f"arn:aws:firehose:{self.config['aws']['region']}:{self.config['aws']['account_id']}:deliverystream/{self.config['firehose']['stream_name']}"
                }]
            },
            "S3Access": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "s3:PutObject",
                        "s3:GetObject"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.config['s3']['raw_bucket']}/*",
                        f"arn:aws:s3:::{self.config['s3']['backup_bucket']}/*"
                    ]
                }]
            }
        }
        
        return self.create_iam_role(role_name, assume_role_policy, policies)
    
    def create_firehose_role(self):
        """Create IAM role for Firehose"""
        role_name = self.config['iam']['firehose_role_name']
        
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "firehose.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        policies = {
            "FirehoseS3Access": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "s3:AbortMultipartUpload",
                        "s3:GetBucketLocation",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:ListBucketMultipartUploads",
                        "s3:PutObject"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.config['s3']['backup_bucket']}",
                        f"arn:aws:s3:::{self.config['s3']['backup_bucket']}/*"
                    ]
                }]
            },
            "FirehoseLogsAccess": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }]
            }
        }
        
        return self.create_iam_role(role_name, assume_role_policy, policies)
    
    def create_lambda_function(self, role_arn):
        """Create Lambda function"""
        function_name = self.config['lambda']['function_name']
        
        # Create deployment package
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write('lambda_function.py', 'lambda_function.py')
        
        zip_buffer.seek(0)
        
        try:
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime=self.config['lambda']['runtime'],
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_buffer.read()},
                Description='Process Meraki webhooks for S3 and Firehose',
                Timeout=self.config['lambda']['timeout_seconds'],
                MemorySize=self.config['lambda']['memory_mb'],
                Environment={
                    'Variables': {
                        'FIREHOSE_STREAM_NAME': self.config['firehose']['stream_name'],
                        'RAW_BUCKET': self.config['s3']['raw_bucket']
                    }
                }
            )
            function_arn = response['FunctionArn']
            print(f"✅ Created Lambda function: {function_name}")
            return function_arn
            
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                response = self.lambda_client.get_function(FunctionName=function_name)
                print(f"ℹ️  Lambda function already exists: {function_name}")
                return response['Configuration']['FunctionArn']
            else:
                print(f"❌ Error creating Lambda function: {e}")
                return None
    
    def create_api_gateway(self, lambda_arn):
        """Create API Gateway REST API"""
        api_name = self.config['api_gateway']['api_name']
        
        try:
            # Create REST API
            api_response = self.apigateway.create_rest_api(
                name=api_name,
                description='Meraki Webhook API',
                endpointConfiguration={'types': ['REGIONAL']}
            )
            api_id = api_response['id']
            print(f"✅ Created API Gateway: {api_name}")
            
            # Get root resource
            resources = self.apigateway.get_resources(restApiId=api_id)
            root_id = resources['items'][0]['id']
            
            # Create /webhook resource
            webhook_resource = self.apigateway.create_resource(
                restApiId=api_id,
                parentId=root_id,
                pathPart='webhook'
            )
            webhook_resource_id = webhook_resource['id']
            
            # Create POST method
            self.apigateway.put_method(
                restApiId=api_id,
                resourceId=webhook_resource_id,
                httpMethod='POST',
                authorizationType='NONE'
            )
            
            # Set Lambda integration
            lambda_uri = f"arn:aws:apigateway:{self.config['aws']['region']}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=webhook_resource_id,
                httpMethod='POST',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=lambda_uri
            )
            
            # Deploy API
            deployment = self.apigateway.create_deployment(
                restApiId=api_id,
                stageName=self.config['api_gateway']['stage_name']
            )
            
            # Add Lambda permission for API Gateway
            try:
                self.lambda_client.add_permission(
                    FunctionName=self.config['lambda']['function_name'],
                    StatementId='apigateway-invoke',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f"arn:aws:execute-api:{self.config['aws']['region']}:{self.config['aws']['account_id']}:{api_id}/*/*"
                )
            except ClientError as e:
                if 'ResourceConflictException' not in str(e):
                    print(f"Warning: Could not add Lambda permission: {e}")
            
            api_url = f"https://{api_id}.execute-api.{self.config['aws']['region']}.amazonaws.com/{self.config['api_gateway']['stage_name']}/webhook"
            print(f"✅ API Gateway URL: {api_url}")
            
            return api_url
            
        except ClientError as e:
            print(f"❌ Error creating API Gateway: {e}")
            return None
    
    def create_firehose_stream(self, role_arn):
        """Create Kinesis Firehose delivery stream"""
        stream_name = self.config['firehose']['stream_name']
        
        try:
            response = self.firehose.create_delivery_stream(
                DeliveryStreamName=stream_name,
                DeliveryStreamType='DirectPut',
                ExtendedS3DestinationConfiguration={
                    'RoleARN': role_arn,
                    'BucketARN': f"arn:aws:s3:::{self.config['s3']['backup_bucket']}",
                    'Prefix': 'firehose-backup/',
                    'ErrorOutputPrefix': 'firehose-errors/',
                    'BufferingHints': {
                        'SizeInMBs': self.config['firehose']['buffer_size_mb'],
                        'IntervalInSeconds': self.config['firehose']['buffer_interval_seconds']
                    },
                    'CompressionFormat': 'GZIP',
                    'CloudWatchLoggingOptions': {
                        'Enabled': True,
                        'LogGroupName': f"/aws/kinesisfirehose/{stream_name}",
                        'LogStreamName': 'S3Delivery'
                    }
                }
            )
            print(f"✅ Created Firehose stream: {stream_name}")
            return response['DeliveryStreamARN']
            
        except ClientError as e:
            if 'ResourceInUseException' in str(e):
                print(f"ℹ️  Firehose stream already exists: {stream_name}")
                response = self.firehose.describe_delivery_stream(DeliveryStreamName=stream_name)
                return response['DeliveryStreamDescription']['DeliveryStreamARN']
            else:
                print(f"❌ Error creating Firehose stream: {e}")
                return None
    
    def deploy(self):
        """Deploy all infrastructure"""
        print("=" * 60)
        print("Deploying Meraki Webhook Streaming Infrastructure")
        print("=" * 60)
        
        # Create S3 buckets
        print("\n1. Creating S3 buckets...")
        self.create_s3_buckets()
        
        # Create IAM roles
        print("\n2. Creating IAM roles...")
        lambda_role_arn = self.create_lambda_role()
        firehose_role_arn = self.create_firehose_role()
        
        if not lambda_role_arn or not firehose_role_arn:
            print("❌ Failed to create IAM roles")
            return False
        
        # Create Lambda function
        print("\n3. Creating Lambda function...")
        lambda_arn = self.create_lambda_function(lambda_role_arn)
        
        if not lambda_arn:
            print("❌ Failed to create Lambda function")
            return False
        
        # Create API Gateway
        print("\n4. Creating API Gateway...")
        api_url = self.create_api_gateway(lambda_arn)
        
        if not api_url:
            print("❌ Failed to create API Gateway")
            return False
        
        # Create Firehose stream
        print("\n5. Creating Firehose stream...")
        firehose_arn = self.create_firehose_stream(firehose_role_arn)
        
        if not firehose_arn:
            print("❌ Failed to create Firehose stream")
            return False
        
        # Save deployment info
        self.deployment_info = {
            'api_url': api_url,
            'lambda_arn': lambda_arn,
            'firehose_arn': firehose_arn,
            'lambda_role_arn': lambda_role_arn,
            'firehose_role_arn': firehose_role_arn,
            'raw_bucket': self.config['s3']['raw_bucket'],
            'backup_bucket': self.config['s3']['backup_bucket']
        }
        
        with open('deployment_info.json', 'w') as f:
            json.dump(self.deployment_info, f, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ Deployment Complete!")
        print("=" * 60)
        print(f"\nWebhook URL: {api_url}")
        print(f"Raw Storage: s3://{self.config['s3']['raw_bucket']}/raw/")
        print(f"Backup Storage: s3://{self.config['s3']['backup_bucket']}/firehose-backup/")
        print("\nDeployment info saved to: deployment_info.json")
        
        return True

if __name__ == "__main__":
    deployer = InfrastructureDeployer()
    deployer.deploy()
