# Git Cleanup Instructions

## Problem
The git repository contains committed credentials that must be removed before pushing to remote.

## Files to Remove from History
- `credentials.yaml` - Contains AWS credentials, Redshift password, SSH password
- Any other credential files that may have been committed

## Solution: Clean History

### Option 1: Using the Cleanup Script (Recommended)

**On macOS (your work computer):**

```bash
cd /path/to/meraki-webhook-streaming
chmod +x clean_git_history.sh
./clean_git_history.sh
```

This script will:
1. Remove credentials.yaml from all git history
2. Remove other credential files (credentials_config.yaml, set_credentials.bat, *.pem)
3. Squash all commits into a single clean initial commit
4. Clean up git references and garbage collect

### Option 2: Manual Cleanup

If you prefer to do it manually:

```bash
# Remove credentials.yaml from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch credentials.yaml" \
  --prune-empty --tag-name-filter cat -- --all

# Remove other credential files
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch credentials_config.yaml set_credentials.bat *.pem" \
  --prune-empty --tag-name-filter cat -- --all

# Clean up
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Option 3: Fresh Start (Simplest)

If this is a new repo or you don't care about history:

```bash
# Remove .git directory
rm -rf .git

# Initialize fresh repo
git init
git add .
git commit -m "Initial commit: Meraki webhook streaming to Redshift"

# Add remote and push
git remote add origin YOUR_REMOTE_URL
git push -u origin main --force
```

## Verification

After cleanup, verify credentials are removed:

```bash
# Check current files
git status

# Check history for credentials.yaml
git log --all --full-history -- credentials.yaml
# Should return nothing

# Search for AWS keys in history
git log -p | grep -i "aws_access_key_id"
# Should return nothing
```

## Before Pushing

1. **Verify credentials.yaml is in .gitignore**
   ```bash
   cat .gitignore | grep credentials.yaml
   ```

2. **Verify credentials.yaml is not staged**
   ```bash
   git status
   # Should show credentials.yaml as untracked or ignored
   ```

3. **Create credentials.yaml on work computer**
   - Copy credentials.yaml from this computer to your work computer
   - Or recreate it with fresh AWS credentials

## Push to Remote

```bash
# Force push (overwrites remote history)
git push origin main --force

# Or if using a different branch
git push origin YOUR_BRANCH --force
```

## Important Notes

- **credentials.yaml is gitignored** - It will never be committed again
- **AWS credentials expire every 30 minutes** - You'll need to refresh them on your work computer
- **VPN required** - Your work computer needs VPN access to run setup_redshift_schema.py
- **Force push required** - Since we're rewriting history, you must force push

## Files That Should Be Committed

✅ Safe to commit:
- config.json (no credentials, just resource names)
- All Python scripts
- README.md
- CLAUDE_DEPLOYMENT_PROMPT.md
- .gitignore
- requirements.txt

❌ Never commit:
- credentials.yaml
- credentials_config.yaml
- set_credentials.bat
- *.pem files
- deployment_info.json (may contain ARNs)
- schema_samples.json (contains real data)

## After Cleanup on Work Computer

1. Pull the cleaned repo
2. Create fresh credentials.yaml with current AWS credentials
3. Connect to VPN
4. Run: `python setup_redshift_schema.py`
5. Run: `python deploy_infrastructure.py`
6. Run: `python test_webhook.py`
