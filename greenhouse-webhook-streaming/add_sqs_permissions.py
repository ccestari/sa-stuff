"""
Add SQS permissions to Lambda IAM role
Utility for fixing AccessDenied errors
"""
import boto3
import json
import os

def add_sqs_permissions(role_name, queue_arn):
    """Add SQS SendMessage permission to IAM role"""
    
    iam = boto3.client('iam', region_name='us-east-1')
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sqs:SendMessage",
                    "sqs:GetQueueUrl"
                ],
                "Resource": queue_arn
            }
        ]
    }
    
    policy_name = 'GreenhouseSQSAccess'
    
    try:
        response = iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        print(f"[OK] Added SQS permissions to role: {role_name}")
        print(f"[OK] Policy name: {policy_name}")
        print(f"[OK] Permissions: sqs:SendMessage, sqs:GetQueueUrl")
        print(f"[OK] Queue: {queue_arn}")
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def verify_permissions(role_name, policy_name='GreenhouseSQSAccess'):
    """Verify SQS permissions were added"""
    
    iam = boto3.client('iam', region_name='us-east-1')
    
    try:
        response = iam.get_role_policy(
            RoleName=role_name,
            PolicyName=policy_name
        )
        print(f"\n[OK] Verified policy exists: {policy_name}")
        print(f"[OK] Policy document:")
        print(json.dumps(response['PolicyDocument'], indent=2))
        return True
    except Exception as e:
        print(f"[ERROR] Could not verify: {e}")
        return False

if __name__ == '__main__':
    # Configuration
    role_name = 'greenhouse-webhook-processor-role'
    queue_arn = 'arn:aws:sqs:us-east-1:309820967897:greenhouse-flattened-records'
    
    print("Adding SQS permissions to Lambda role...")
    if add_sqs_permissions(role_name, queue_arn):
        print("\nVerifying permissions...")
        verify_permissions(role_name)
