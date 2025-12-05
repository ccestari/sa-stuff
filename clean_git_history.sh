#!/bin/bash
# Script to clean git history and remove credentials
# Run this before pushing to remote

echo "=========================================="
echo "Git History Cleanup Script"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Remove credentials.yaml from git history"
echo "2. Remove any committed AWS credentials"
echo "3. Squash all commits into a clean initial commit"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

# Backup current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Remove credentials.yaml from history if it exists
echo ""
echo "Removing credentials.yaml from git history..."
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch credentials.yaml" \
  --prune-empty --tag-name-filter cat -- --all

# Remove any files with AWS credentials patterns
echo ""
echo "Removing files with credential patterns..."
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch credentials_config.yaml set_credentials.bat *.pem" \
  --prune-empty --tag-name-filter cat -- --all

# Create orphan branch for clean history
echo ""
echo "Creating clean history..."
git checkout --orphan clean_history

# Add all files
git add -A

# Create initial commit
git commit -m "Initial commit: Meraki webhook streaming to Redshift

- API Gateway → Lambda → Firehose → Redshift architecture
- Flexible schema supporting 24+ alert types
- Historical data analysis (3,336 files analyzed)
- Enhanced Lambda with schema detection and alerting
- Cross-account S3 copy capability
- Production config: db02 database, edna-stream-meraki bucket
- VPN required for Redshift access via SSH bastion"

# Delete old branch
git branch -D $CURRENT_BRANCH

# Rename clean branch to original name
git branch -m $CURRENT_BRANCH

# Force garbage collection
echo ""
echo "Cleaning up..."
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "=========================================="
echo "✅ Git history cleaned!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify files: git log --oneline"
echo "2. Check credentials removed: git log --all --full-history -- credentials.yaml"
echo "3. Force push: git push origin $CURRENT_BRANCH --force"
echo ""
echo "⚠️  WARNING: This will overwrite remote history!"
echo ""
