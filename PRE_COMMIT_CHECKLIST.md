# Pre-Commit Checklist

Before committing and pushing to GitHub, verify:

## 🔐 Security

- [ ] `credentials.yaml` is NOT in repo
- [ ] `credentials_config.yaml` is NOT in repo
- [ ] No AWS credentials in any files
- [ ] No passwords in any files
- [ ] `.gitignore` includes all sensitive files
- [ ] Run: `python verify_no_credentials.py`

## 📝 Documentation

- [ ] `README.md` is up to date
- [ ] `FINAL_STATUS.md` reflects current state
- [ ] `CLAUDE_DEPLOYMENT_PROMPT.md` is complete
- [ ] `CONVERSATION_LOG.md` is saved
- [ ] All scripts have docstrings

## 🧹 Cleanup

- [ ] Remove duplicate JSON files in root
- [ ] Remove temporary/test files
- [ ] Remove `__pycache__` directories
- [ ] Remove `.pyc` files
- [ ] Remove log files

## ✅ Testing

- [ ] `python check_s3_data.py` works
- [ ] `python test_webhook.py` works
- [ ] All Python files have no syntax errors
- [ ] `requirements.txt` is complete

## 📦 Files to Keep

### Core
- `lambda_function.py`
- `setup_redshift_schema.py`
- `deploy_infrastructure.py`
- `config.json`

### Sync
- `sync_s3_to_redshift.py`
- `sync_s3_to_redshift.sh`
- `load_s3_to_redshift.py`

### Monitoring
- `check_s3_data.py`
- `check_lambda_logs.py`
- `check_status.py`
- `test_webhook.py`

### Configuration
- `requirements.txt`
- `credentials.yaml.template`
- `.gitignore`

### Documentation
- `README.md`
- `FINAL_STATUS.md`
- `CLAUDE_DEPLOYMENT_PROMPT.md`
- `CONVERSATION_LOG.md`
- `PRE_COMMIT_CHECKLIST.md`

### Samples
- `sample_payloads/` directory

## 🗑️ Files to Remove

- [ ] `meraki-webhooks-to-s3-*.json` (in root, keep in sample_payloads/)
- [ ] `*-Copy*.json`
- [ ] `credentials.yaml` (if accidentally added)
- [ ] `credentials_config.yaml`
- [ ] `deployment_info.json`
- [ ] `*.log` files
- [ ] `__pycache__/`
- [ ] `.DS_Store`
- [ ] `meraki_flat.csv`
- [ ] `meraki_test_data/`
- [ ] `insert_into_meraki`
- [ ] `*.ipynb` (Jupyter notebooks)
- [ ] `*.pyc`

## 🚀 Git Commands

```bash
# Check status
git status

# Add files
git add .

# Commit
git commit -m "Final working version - S3 to Redshift sync"

# Push
git push origin main
```

## ⚠️ CRITICAL

**NEVER commit `credentials.yaml`!**

If accidentally committed:
```bash
git rm --cached credentials.yaml
git commit -m "Remove credentials"
git push origin main
```

Then rotate all credentials immediately!
