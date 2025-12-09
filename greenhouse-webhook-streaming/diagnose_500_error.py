"""
Diagnostic tool for analyzing Lambda errors
Useful for troubleshooting webhook failures
"""
import json

def analyze_error_logs(log_file='lambda_logs.txt'):
    """Analyze Lambda logs for common error patterns"""
    
    errors = {
        'none_body': 0,
        'context_error': 0,
        'sqs_permission': 0,
        'other': 0
    }
    
    print("=" * 80)
    print("LAMBDA ERROR ANALYSIS")
    print("=" * 80)
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
            
            # Check for None body errors
            if "'NoneType' object has no attribute 'get'" in content:
                errors['none_body'] = content.count("'NoneType' object has no attribute 'get'")
                print(f"\n[ERROR] None body handling: {errors['none_body']} occurrences")
                print("  Fix: Handle None/empty body in Lambda")
            
            # Check for context errors
            if "request_id" in content and "AttributeError" in content:
                errors['context_error'] = content.count("request_id")
                print(f"\n[ERROR] Context attribute: {errors['context_error']} occurrences")
                print("  Fix: Use context.aws_request_id instead of context.request_id")
            
            # Check for SQS permission errors
            if "AccessDenied" in content and "sqs:sendmessage" in content.lower():
                errors['sqs_permission'] = content.count("AccessDenied")
                print(f"\n[ERROR] SQS permissions: {errors['sqs_permission']} occurrences")
                print("  Fix: Add sqs:SendMessage permission to Lambda role")
            
            # Count 500 errors
            error_500_count = content.count("500")
            print(f"\n[INFO] HTTP 500 errors found: {error_500_count}")
            
            # Count successful requests
            success_count = content.count("200")
            print(f"[INFO] HTTP 200 success: {success_count}")
            
    except FileNotFoundError:
        print(f"\n[ERROR] Log file not found: {log_file}")
        print("Run: aws logs tail /aws/lambda/greenhouse-webhook-processor --region us-east-1 > lambda_logs.txt")
    
    print("\n" + "=" * 80)
    return errors

if __name__ == '__main__':
    analyze_error_logs()
