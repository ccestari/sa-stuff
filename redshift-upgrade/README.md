# Redshift Cluster Upgrade Utilities

Safely upgrade Redshift cluster one major version at a time with monitoring and snapshots.

## Current Cluster
- **Cluster**: edna-prod-dw
- **Current Version**: 8.0.2
- **ARN**: arn:aws:redshift:us-east-1:309820967897:namespace:e32e8f17-2e92-4e59-9bff-33c3cbf38a72

## Scripts

### 1. redshift_monitor.py
Analyzes CloudWatch metrics to recommend maintenance windows.

```bash
python3 redshift_monitor.py
```

**Output:**
- Hourly connection, CPU, and network patterns
- Recommended low-activity time windows

### 2. redshift_upgrade.py
Performs one major version upgrade with snapshot backup.

```bash
python3 redshift_upgrade.py
```

**Process:**
1. Creates timestamped snapshot
2. Upgrades one major version
3. Waits for completion
4. Provides rollback snapshot ID

## Upgrade Strategy

1. **Day 0**: Run monitor → identify maintenance window
2. **Day 1**: Upgrade 8.0.2 → 9.0 (wait 24 hours)
3. **Day 2**: Monitor for issues
4. **Day 3**: Upgrade 9.0 → 10.0 (wait 24 hours)
5. Continue until reaching latest version

## Configuration

- `config.json` - Cluster details
- `credentials.yaml` - AWS credentials (rotate every 30 min)

## Requirements

```bash
pip install boto3 pyyaml
```

## Notes

- Cluster is read-only during upgrade (30-60 min)
- Snapshots enable rollback if needed
- Test applications after each upgrade
