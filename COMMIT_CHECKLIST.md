# Git Commit Checklist

## Before Committing

### 1. Verify Credentials Are Not Staged

```bash
git status
```

**Should NOT see:**
- credentials.yaml
- credentials_config.yaml
- set_credentials.bat
- init_credentials.bat
- *.pem files

**Should see (untracked or ignored):**
- credentials.yaml (if it exists)

### 2. Verify .gitignore Is Correct

```bash
cat .gitignore | grep -E "credentials|pem|key"
```

Should show:
```
credentials_config.yaml
credentials.yaml
set_credentials.bat
init_credentials.bat
*.pem
*.key
```

### 3. Clean Git History (REQUIRED)

**You MUST clean git history before pushing because credentials were previously committed.**

Choose one method:

#### Method A: Use Cleanup Script (Recommended)
```bash
chmod +x clean_git_history.sh
./clean_git_history.sh
```

#### Method B: Fresh Start (Simplest)
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit: Meraki webhook streaming to Redshift"
```

### 4. Verify No Credentials in History

```bash
# Check for credentials.yaml in history
git log --all --full-history -- credentials.yaml
# Should return nothing

# Search for AWS keys
git log -p | grep -i "ASIA" | head -5
# Should return nothing

# Search for passwords
git log -p | grep -i "password" | head -5
# Should only show comments/documentation, not actual passwords
```

## Committing

### 1. Stage Files

```bash
git add .
```

### 2. Review What's Being Committed

```bash
git status
git diff --cached
```

**Verify:**
- ✅ credentials.yaml is NOT in the list
- ✅ All Python scripts are included
- ✅ README.md and documentation files are included
- ✅ config.json is included (it's safe - no credentials)

### 3. Commit

```bash
git commit -m "Initial commit: Meraki webhook streaming to Redshift

- API Gateway → Lambda → Firehose → Redshift architecture
- Flexible schema supporting 24+ alert types
- Historical data analysis (3,336 files analyzed)
- Enhanced Lambda with schema detection and alerting
- Cross-account S3 copy capability
- Production config: db02 database, edna-stream-meraki bucket
- VPN required for Redshift access via SSH bastion"
```

## Pushing to Remote

### 1. Add Remote (if not already added)

```bash
git remote add origin YOUR_REPO_URL
```

### 2. Force Push (Required if history was cleaned)

```bash
git push origin main --force
```

**⚠️ WARNING**: Force push will overwrite remote history. Make sure you've cleaned the history first!

## After Pushing

### 1. Verify on Remote

- Check GitHub/GitLab/etc. to verify files are there
- Verify credentials.yaml is NOT visible
- Check commit history is clean

### 2. Clone on Work Computer

```bash
git clone YOUR_REPO_URL
cd meraki-webhook-streaming
```

### 3. Create credentials.yaml on Work Computer

```bash
cp credentials.yaml.template credentials.yaml
# Edit with fresh credentials
```

## Files That Should Be Committed

### ✅ Safe to Commit

**Python Scripts:**
- lambda_function.py
- deploy_infrastructure.py
- setup_redshift_schema.py
- test_webhook.py
- analyze_historical_data.py
- copy_historical_data.py
- setup_credentials.py

**Configuration:**
- config.json (no credentials)
- requirements.txt
- .gitignore

**Documentation:**
- README.md
- CLAUDE_DEPLOYMENT_PROMPT.md
- WORK_COMPUTER_SETUP.md
- GIT_CLEANUP_INSTRUCTIONS.md
- COMMIT_CHECKLIST.md

**Templates:**
- credentials.yaml.template

**Scripts:**
- clean_git_history.sh

### ❌ NEVER Commit

**Credentials:**
- credentials.yaml
- credentials_config.yaml
- set_credentials.bat
- init_credentials.bat
- *.pem
- *.key

**Generated Files:**
- deployment_info.json (may contain ARNs)
- schema_samples.json (contains real data)
- __pycache__/
- *.pyc

**Sample Data:**
- meraki-webhooks-to-s3-*.json (real webhook data)

## Emergency: Credentials Were Pushed

If you accidentally pushed credentials:

### 1. Immediately Rotate Credentials
- Get new AWS credentials from SSO
- Change Redshift password
- Change SSH password

### 2. Clean History and Force Push
```bash
./clean_git_history.sh
git push origin main --force
```

### 3. Verify Credentials Are Gone
```bash
git log --all --full-history -- credentials.yaml
```

## Final Verification

Before considering this done:

- [ ] Git history is clean (no credentials in any commit)
- [ ] credentials.yaml is in .gitignore
- [ ] credentials.yaml is NOT staged or committed
- [ ] Pushed to remote successfully
- [ ] Verified on remote that credentials.yaml is not visible
- [ ] Can clone on work computer
- [ ] credentials.yaml.template exists for easy setup

## Ready to Push?

Run this final check:

```bash
# Check status
git status

# Check history for credentials
git log --all --full-history -- credentials.yaml

# Check for AWS keys in history
git log -p | grep -i "ASIA" | wc -l
# Should be 0

# If all clear, push!
git push origin main --force
```
