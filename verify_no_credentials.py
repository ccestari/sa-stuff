#!/usr/bin/env python3
"""
Verify no credentials in files before git commit
"""
import os
import re

# Patterns to search for
CREDENTIAL_PATTERNS = [
    (r'ASIA[A-Z0-9]{16}', 'AWS Access Key'),
    (r'aws_access_key_id\s*=\s*[A-Z0-9]{20}', 'AWS Access Key'),
    (r'aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}', 'AWS Secret Key'),
    (r'IQoJb3JpZ2luX2VjE[A-Za-z0-9/+=]{200,}', 'AWS Session Token'),
    (r'password\s*[:=]\s*[^\s<>]{8,}', 'Password'),
]

# Files to check
FILES_TO_CHECK = [
    'config.json',
    'lambda_function.py',
    'deploy_infrastructure.py',
    'setup_redshift_schema.py',
    'test_webhook.py',
    'README.md',
    'CLAUDE_DEPLOYMENT_PROMPT.md',
]

# Files that should NOT exist or be committed
FORBIDDEN_FILES = [
    'credentials.yaml',
    'credentials_config.yaml',
    'set_credentials.bat',
    'deployment_info.json',
]

def check_file(filepath):
    """Check a file for credential patterns"""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern, name in CREDENTIAL_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    # Exclude template placeholders
                    real_matches = [m for m in matches if not any(
                        placeholder in m.upper() 
                        for placeholder in ['YOUR_', 'PLACEHOLDER', 'EXAMPLE', 'TEMPLATE']
                    )]
                    if real_matches:
                        issues.append(f"  ❌ Found {name}: {real_matches[0][:20]}...")
    except Exception as e:
        issues.append(f"  ⚠️  Error reading file: {e}")
    return issues

def main():
    print("=" * 60)
    print("Credential Verification")
    print("=" * 60)
    
    all_issues = []
    
    # Check files for credentials
    print("\n1. Checking files for credentials...")
    for filepath in FILES_TO_CHECK:
        if os.path.exists(filepath):
            print(f"\n  Checking {filepath}...")
            issues = check_file(filepath)
            if issues:
                all_issues.extend(issues)
                for issue in issues:
                    print(issue)
            else:
                print(f"  ✅ Clean")
    
    # Check for forbidden files
    print("\n2. Checking for forbidden files...")
    for filepath in FORBIDDEN_FILES:
        if os.path.exists(filepath):
            print(f"  ❌ Found: {filepath} (should be gitignored)")
            all_issues.append(f"Forbidden file exists: {filepath}")
        else:
            print(f"  ✅ Not found: {filepath}")
    
    # Check .gitignore
    print("\n3. Checking .gitignore...")
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore = f.read()
            required = ['credentials.yaml', '*.pem', '*.key']
            for item in required:
                if item in gitignore:
                    print(f"  ✅ {item} is gitignored")
                else:
                    print(f"  ❌ {item} NOT in .gitignore")
                    all_issues.append(f"{item} not in .gitignore")
    
    # Summary
    print("\n" + "=" * 60)
    if all_issues:
        print("❌ VERIFICATION FAILED")
        print("=" * 60)
        print("\nIssues found:")
        for issue in all_issues:
            print(f"  - {issue}")
        print("\n⚠️  DO NOT COMMIT until issues are resolved!")
        return 1
    else:
        print("✅ VERIFICATION PASSED")
        print("=" * 60)
        print("\nNo credentials found. Safe to commit!")
        return 0

if __name__ == '__main__':
    exit(main())
