#!/usr/bin/env python3
"""
Manage AWS credentials with 30-minute rotation support
"""
import os
import yaml
import boto3
from pathlib import Path
from datetime import datetime

class CredentialManager:
    """Manage AWS credentials from environment with YAML config storage"""
    
    def __init__(self, config_file='credentials_config.yaml'):
        self.config_file = config_file
        self.credentials = {}
        
    def load_from_env(self):
        """Load credentials from environment variables"""
        required = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        
        for key in required:
            if key not in os.environ:
                return False
        
        self.credentials = {
            'aws_access_key_id': os.environ['AWS_ACCESS_KEY_ID'],
            'aws_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY'],
            'aws_session_token': os.environ.get('AWS_SESSION_TOKEN')
        }
        
        # Save to YAML config
        self.save_to_yaml()
        return True
    
    def save_to_yaml(self):
        """Save credentials to YAML config file"""
        config = {
            'aws_credentials': self.credentials,
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'redshift_password': os.environ.get('REDSHIFT_PASSWORD'),
            'ssh_password': os.environ.get('SSH_PASSWORD')
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def load_from_yaml(self):
        """Load credentials from YAML config file"""
        if not Path(self.config_file).exists():
            return False
        
        with open(self.config_file) as f:
            config = yaml.safe_load(f)
        
        if config and 'aws_credentials' in config:
            self.credentials = config['aws_credentials']
            return True
        return False
    
    def load_credentials(self):
        """Load credentials from environment or YAML"""
        if self.load_from_env():
            return True
        return self.load_from_yaml()
    
    def are_credentials_valid(self):
        """Check if credentials are valid by making an AWS call"""
        try:
            session = self.get_boto3_session()
            sts = session.client('sts')
            sts.get_caller_identity()
            return True
        except Exception:
            return False
    
    def get_boto3_session(self):
        """Get boto3 session with credentials"""
        return boto3.Session(**self.credentials)
    
    def display_status(self):
        """Display credential status"""
        if not self.credentials:
            print("❌ No credentials loaded")
            return
        
        try:
            session = self.get_boto3_session()
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            print("✅ Credentials valid")
            print(f"   Account: {identity['Account']}")
            print(f"   User: {identity['Arn']}")
        except Exception as e:
            print(f"❌ Credentials invalid: {e}")

def setup_credentials():
    """Interactive setup of AWS credentials"""
    print("AWS Credentials Setup - Meraki Webhook Streaming")
    print("=" * 60)
    print("\nCredentials should be set via environment variables:")
    print("  - AWS_ACCESS_KEY_ID")
    print("  - AWS_SECRET_ACCESS_KEY")
    print("  - AWS_SESSION_TOKEN (optional)")
    print("\nFor Redshift and SSH:")
    print("  - REDSHIFT_PASSWORD")
    print("  - SSH_PASSWORD")
    
    print("\nChoose setup method:")
    print("1. Create batch file to set environment variables")
    print("2. Display instructions for manual setup")
    print("3. Check current credentials")
    print("4. Refresh credentials from environment")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        create_env_batch_file()
    elif choice == "2":
        display_instructions()
    elif choice == "3":
        check_credentials()
    elif choice == "4":
        refresh_credentials()
    else:
        print("Invalid choice. Please run the script again.")

def create_env_batch_file():
    """Create batch file template for setting environment variables"""
    batch_content = """@echo off
REM AWS Credentials - Update with your current credentials
REM These expire every ~30 minutes, get new ones from AWS SSO

echo Setting AWS Credentials for Meraki Webhook Streaming...
set AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_HERE
set AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY_HERE
set AWS_SESSION_TOKEN=YOUR_SESSION_TOKEN_HERE

REM Redshift and SSH passwords
set REDSHIFT_PASSWORD=YOUR_REDSHIFT_PASSWORD
set SSH_PASSWORD=YOUR_SSH_PASSWORD

echo Credentials set for this session.
echo Remember to update AWS credentials when they expire!
"""
    
    with open('set_credentials.bat', 'w') as f:
        f.write(batch_content)
    
    print("\n✅ Created: set_credentials.bat")
    print("\nEdit this file with your current AWS credentials, then run it before using other scripts.")

def display_instructions():
    """Display manual setup instructions"""
    print("\n" + "=" * 60)
    print("MANUAL SETUP INSTRUCTIONS")
    print("=" * 60)
    print("\n1. Get AWS credentials from SSO:")
    print("   https://d-9067640efb.awsapps.com/start/#")
    print("\n2. Set environment variables (Windows):")
    print("   set AWS_ACCESS_KEY_ID=<your-access-key>")
    print("   set AWS_SECRET_ACCESS_KEY=<your-secret-key>")
    print("   set AWS_SESSION_TOKEN=<your-session-token>")
    print("\n3. Set passwords:")
    print("   set REDSHIFT_PASSWORD=<your-password>")
    print("   set SSH_PASSWORD=<your-ssh-password>")
    print("\n4. Run your scripts in the same terminal session")

def check_credentials():
    """Check current credentials"""
    print("\n" + "=" * 60)
    print("CHECKING CREDENTIALS")
    print("=" * 60)
    
    manager = CredentialManager()
    
    if manager.load_credentials():
        manager.display_status()
    else:
        print("\n❌ No credentials found in environment or config file")
        print("\nSet these environment variables:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        print("  - AWS_SESSION_TOKEN")

def refresh_credentials():
    """Refresh credentials from environment"""
    print("\n" + "=" * 60)
    print("REFRESHING CREDENTIALS")
    print("=" * 60)
    
    manager = CredentialManager()
    
    if manager.load_from_env():
        print("\n✅ Credentials refreshed from environment")
        manager.display_status()
    else:
        print("\n❌ Could not load credentials from environment")
        print("\nMake sure these environment variables are set:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        print("  - AWS_SESSION_TOKEN")

if __name__ == "__main__":
    setup_credentials()
