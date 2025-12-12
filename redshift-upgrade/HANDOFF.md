# Redshift Upgrade Project - Session Handoff

## Current Status: ✅ Analysis Complete, Ready for Upgrade

### What We Accomplished
1. **Created monitoring script** (`redshift_monitor.py`) - Analyzes CloudWatch metrics to find optimal maintenance windows
2. **Created upgrade script** (`redshift_upgrade.py`) - Performs incremental major version upgrades with snapshots
3. **Ran 7-day analysis** - Identified optimal maintenance window: **Sunday 01:00-04:00 UTC**
4. **Generated detailed report** (`ANALYSIS_REPORT.md`) with activity patterns and recommendations

### Current Cluster State
- **Cluster**: edna-prod-dw
- **Current Version**: 1.0 (PostgreSQL 8.0.2 compatible)
- **Status**: Available
- **Current Maintenance Window**: Sunday 06:00-06:30 UTC (too short for major upgrades)
- **Recommended Window**: Sunday 01:00-04:00 UTC (lowest activity: 7-11 connections, 6-8% CPU)

### Key Findings from Analysis
- **Peak Activity**: 12:00-13:00 UTC (42 connections, 50% CPU, 159 MB/s)
- **Lowest Activity**: 01:00-04:00 UTC (7-11 connections, 6-8% CPU, 10-12 MB/s)
- **No Zero-Activity Periods**: Cluster used 24/7
- **Current Window Too Short**: 30 minutes insufficient for major version upgrades (need 2-3 hours)

## Next Steps

### Option 1: Proceed with Upgrade (Recommended)
```bash
cd /Users/chris.cestari/Documents/GitHub/sa-stuff/redshift-upgrade

# 1. Update AWS credentials (they expire every 30 min)
# Edit credentials.yaml with fresh credentials from AWS SSO

# 2. Run upgrade script (upgrades one major version at a time)
python3 redshift_upgrade.py

# 3. Wait 24 hours and test applications

# 4. Repeat for next version (1.0 → 2.0 → 3.0)
```

### Option 2: Change Maintenance Window First
Before upgrading, extend maintenance window to 2-3 hours:
- **Recommended**: Sunday 01:00-04:00 UTC
- Use AWS Console or CLI to modify cluster maintenance window

### Option 3: Re-run Analysis
If you want fresh data or different time period:
```bash
# Analyze last 14 days instead of 7
python3 redshift_monitor.py --days 14

# Analyze last 30 days
python3 redshift_monitor.py --days 30
```

## Important Notes

### AWS Credentials
- **Expire every 30 minutes**
- Stored in `credentials.yaml`
- Get fresh credentials from: https://d-9067640efb.awsapps.com/start/#
- Account: 309820967897 (production)

### Upgrade Strategy
- **One major version at a time**: 1.0 → 2.0 → 3.0
- **Snapshot before each upgrade**: Auto-created with timestamp
- **Wait 24 hours between upgrades**: Test application compatibility
- **Monitor during upgrade**: Script shows progress and waits for completion

### "Allow Version Upgrade" Setting
- **Only affects MINOR versions** (automatic patches)
- **Does NOT affect MAJOR versions** (always manual)
- Current setting doesn't need to change for major version upgrades

## Files in This Project

```
redshift-upgrade/
├── config.json              # Cluster configuration
├── credentials.yaml         # AWS credentials (rotate every 30 min)
├── redshift_monitor.py      # CloudWatch metrics analysis
├── redshift_upgrade.py      # Incremental upgrade script
├── README.md               # Usage instructions
├── ANALYSIS_REPORT.md      # 7-day activity analysis results
└── HANDOFF.md             # This file
```

## Quick Commands Reference

```bash
# Check current cluster version
aws redshift describe-clusters \
  --cluster-identifier edna-prod-dw \
  --query 'Clusters[0].ClusterVersion'

# Run monitoring analysis
python3 redshift_monitor.py

# Perform upgrade (one version at a time)
python3 redshift_upgrade.py

# Check upgrade status
aws redshift describe-clusters \
  --cluster-identifier edna-prod-dw \
  --query 'Clusters[0].[ClusterStatus,ClusterVersion]'
```

## Troubleshooting

### Credentials Expired
```bash
# Update credentials.yaml with fresh credentials from AWS SSO
# Then re-run your command
```

### Upgrade Takes Too Long
- Major version upgrades can take 1-3 hours
- Script waits automatically and shows progress
- Don't interrupt - let it complete

### Need to Rollback
```bash
# Restore from snapshot created before upgrade
aws redshift restore-from-cluster-snapshot \
  --cluster-identifier edna-prod-dw \
  --snapshot-identifier <snapshot-name>
```

## Contact/Resources
- AWS Redshift Documentation: https://docs.aws.amazon.com/redshift/
- Cluster ARN: arn:aws:redshift:us-east-1:309820967897:namespace:e32e8f17-2e92-4e59-9bff-33c3cbf38a72
- Region: us-east-1
- Account: 309820967897

---

**Last Updated**: December 10, 2025
**Session Status**: Analysis complete, ready for upgrade execution
**Recommended Action**: Update maintenance window, then run `redshift_upgrade.py`
