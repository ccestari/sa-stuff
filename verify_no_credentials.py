#!/usr/bin/env python3
"""
Verify no credentials are in git-tracked files
Run before committing to GitHub
"""
import os
import re
import subprocess

# Patterns that indicate credentials
CREDENTIAL_PATTERNS = [
    r'ASIA[A-Z0-9]{16}',  # AWS access key
    r'aws_access_key_id\s*[:=]\s*[A-Z0-9]{20}',
    r'aws_secret_access_key\s*[:=]\s*[A-Za-z0-9/+=]{40}',
    r'aws_session_token\s*[:=]\s*[A-Za-z0-9/+=]{100,}',
    r'password\s*[:=]\s*[\'"][^\'"]+[\'"]',
    r'Cc@succ123',  # Specific password
    r'1faLp42x7Vf161670',  # SSH password
]

# Files to skip
SKIP_FILES = [
    'verify_no_credentials.py',
    'credentials.yaml.template',
    '.gitignore',
    'PRE_COMMIT_CHECKLIST.md',
    'CLAUDE_DEPLOYMENT_PROMPT.md',
    'CONVERSATION_LOG.md',
]

def get_git_files():
    """Get list of files tracked by git"""
    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')
    except:
        # If git not available, scan all Python files
        files = []
        for root, dirs, filenames in os.walk('.'):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
            for filename in filenames:
                if filename.endswith(('.py', '.json', '.yaml', '.yml', '.md', '.sh', '.bat')):
                    files.append(os.path.join(root, filename))
        return files

def check_file(filepath):
    """Check file for credential patterns"""
    if any(skip in filepath for skip in SKIP_FILES):
        return []
    
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in CREDENTIAL_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append((i, line.strip()[:80]))
    except:
        pass
    
    return findings

def main():
    print("=" * 60)
    print("Credential Verification")
    print("=" * 60)
    print()
    
    files = get_git_files()
    issues_found = False
    
    for filepath in files:
        if not os.path.exists(filepath):
            continue
            
        findings = check_file(filepath)
        if findings:
            issues_found = True
            print(f"❌ {filepath}")
            for line_num, line_content in findings:
                print(f"   Line {line_num}: {line_content}")
            print()
    
    if not issues_found:
        print("✅ No credentials found in tracked files")
        print()
        print("Safe to commit!")
        return 0
    else:
        print("=" * 60)
        print("⚠️  CREDENTIALS FOUND!")
        print("=" * 60)
        print()
        print("DO NOT COMMIT until these are removed!")
        return 1

if __name__ == "__main__":
    exit(main())
