#!/usr/bin/env python3
"""AWS Credential Manager - validates and refreshes credentials"""
import boto3
import yaml
from pathlib import Path


class CredentialManager:
    def __init__(self, credentials_file='credentials.yaml'):
        self.credentials_file = credentials_file
        self.creds = None
        
    def load_credentials(self):
        if not Path(self.credentials_file).exists():
            raise FileNotFoundError(f"{self.credentials_file} not found")
        with open(self.credentials_file) as f:
            self.creds = yaml.safe_load(f)
        return self.creds
    
    def validate_credentials(self, environment='production'):
        if not self.creds:
            self.load_credentials()
        env_creds = self.creds.get(environment, {})
        try:
            session = boto3.Session(
                aws_access_key_id=env_creds['aws_access_key_id'],
                aws_secret_access_key=env_creds['aws_secret_access_key'],
                aws_session_token=env_creds.get('aws_session_token'),
                region_name='us-east-1'
            )
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            return True, identity
        except Exception as e:
            return False, str(e)
    
    def prompt_for_credentials(self, environment='production'):
        print(f"\n⚠️  AWS credentials for {environment} are invalid or expired")
        print("Please enter new credentials:")
        access_key = input("AWS_ACCESS_KEY_ID: ").strip()
        secret_key = input("AWS_SECRET_ACCESS_KEY: ").strip()
        session_token = input("AWS_SESSION_TOKEN: ").strip()
        
        if not access_key or not secret_key:
            raise ValueError("Access key and secret key are required")
        
        if not self.creds:
            self.creds = {}
        if environment not in self.creds:
            self.creds[environment] = {}
        
        self.creds[environment]['aws_access_key_id'] = access_key
        self.creds[environment]['aws_secret_access_key'] = secret_key
        if session_token:
            self.creds[environment]['aws_session_token'] = session_token
        
        with open(self.credentials_file, 'w') as f:
            yaml.dump(self.creds, f, default_flow_style=False)
        print("✅ Credentials updated\n")
    
    def ensure_valid_credentials(self, environment='production'):
        valid, result = self.validate_credentials(environment)
        if valid:
            print(f"✅ AWS credentials valid - Account: {result['Account']}")
            return True
        print(f"❌ Credentials invalid: {result}")
        self.prompt_for_credentials(environment)
        valid, result = self.validate_credentials(environment)
        if not valid:
            raise Exception(f"Credentials still invalid: {result}")
        print(f"✅ New credentials validated - Account: {result['Account']}")
        return True
    
    def get_session(self, environment='production'):
        if not self.creds:
            self.load_credentials()
        env_creds = self.creds[environment]
        return boto3.Session(
            aws_access_key_id=env_creds['aws_access_key_id'],
            aws_secret_access_key=env_creds['aws_secret_access_key'],
            aws_session_token=env_creds.get('aws_session_token'),
            region_name='us-east-1'
        )
