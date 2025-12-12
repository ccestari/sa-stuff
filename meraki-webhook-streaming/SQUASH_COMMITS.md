# How to Squash Commits

## Method 1: Reset and Recommit (Simplest)

```bash
cd c:\Users\cesta\source\repos\sa-stuff\meraki-webhook-streaming

# Backup current branch name
git branch

# Create backup branch (optional)
git branch backup-before-squash

# Reset to first commit (or use git reset --soft HEAD~N where N is number of commits to squash)
git reset --soft $(git rev-list --max-parents=0 HEAD)

# Or reset to specific number of commits back
# git reset --soft HEAD~10

# All changes now staged, create single commit
git commit -m "Initial commit: Meraki webhook streaming to Redshift

- API Gateway → Lambda → Firehose → Redshift architecture
- Flexible schema supporting 24+ alert types
- Historical data analysis (3,336 files analyzed)
- Enhanced Lambda with schema detection and alerting
- Cross-account S3 copy capability
- Production config: db02 database, edna-stream-meraki bucket
- VPN required for Redshift access via SSH bastion"

# Force push
git push origin main --force
```

## Method 2: Interactive Rebase

```bash
# Squash last N commits (replace N with number)
git rebase -i HEAD~N

# In editor, change 'pick' to 'squash' (or 's') for all commits except first
# Save and exit
# Edit commit message
# Save and exit

# Force push
git push origin main --force
```

## Method 3: Fresh Start (Nuclear Option)

```bash
cd c:\Users\cesta\source\repos\sa-stuff\meraki-webhook-streaming

# Delete git history
rmdir /s /q .git

# Start fresh
git init
git add .
git commit -m "Initial commit: Meraki webhook streaming to Redshift"

# Add remote and force push
git remote add origin YOUR_REPO_URL
git push -u origin main --force
```

## Before Squashing

Verify credentials.yaml is not staged:
```bash
git status
```

Should NOT show credentials.yaml.

## After Squashing

Verify clean history:
```bash
git log --oneline
```

Should show single commit (or very few commits).

Verify no credentials in history:
```bash
git log --all --full-history -- credentials.yaml
```

Should return nothing.

## Recommended: Method 1

Fastest and safest for your situation.
