# Redshift Cluster Activity Analysis Report
**Date**: December 10, 2025  
**Cluster**: edna-prod-dw  
**Analysis Period**: December 3-10, 2025 (7 days)

## Current Configuration
- **Version**: 1.0 (PostgreSQL 8.0.2 compatible)
- **Status**: Available
- **Current Maintenance Window**: Sunday 06:00-06:30 UTC

## Activity Patterns (UTC)

### Peak Hours (High Activity - AVOID)
- **12:00-13:00**: 42-41 connections, 50% CPU, 159 MB/s network ⚠️ BUSIEST
- **14:00-17:00**: 39-48 connections, 18-20% CPU, 30-46 MB/s network
- **18:00-21:00**: 32-38 connections, 12-22% CPU, 13-45 MB/s network

### Moderate Activity
- **05:00**: 45 connections (spike), 10% CPU
- **22:00**: 17 connections, 17% CPU, 41 MB/s network

### Low Activity Hours (Best for Maintenance)
- **00:00-04:00**: 7-11 connections, 6-8% CPU, 0.7-3.6 MB/s network ✅
- **06:00-09:00**: 13-16 connections, 7-11% CPU, 1.6-8.8 MB/s network ✅
- **23:00**: 12 connections, 11% CPU, 3.5 MB/s network ✅

## Recommendations

### Option 1: Early Morning (RECOMMENDED)
**Time**: Sunday 01:00-04:00 UTC  
**Why**: Lowest connection count (7-11), minimal CPU (6-8%), low network activity  
**Duration**: 3-hour window for upgrade + buffer

### Option 2: Current Window (Acceptable)
**Time**: Sunday 06:00-06:30 UTC (current setting)  
**Why**: Moderate activity (16 connections, 7% CPU)  
**Note**: May need to extend window to 2 hours for major version upgrade

### Option 3: Late Night
**Time**: Sunday 23:00-02:00 UTC  
**Why**: Declining activity pattern, 12 connections, 11% CPU

## Upgrade Plan

### Phase 1: Version 1.0 → 2.0
- **Recommended Window**: Sunday 01:00 UTC
- **Expected Duration**: 30-60 minutes
- **Monitor**: 24 hours post-upgrade

### Phase 2: Version 2.0 → 3.0
- **Recommended Window**: Following Sunday 01:00 UTC
- **Expected Duration**: 30-60 minutes
- **Monitor**: 24 hours post-upgrade

### Continue Pattern
Repeat weekly until reaching latest version.

## Action Items

1. ✅ **Completed**: Activity analysis
2. **Next**: Adjust maintenance window to Sunday 01:00-04:00 UTC
3. **Next**: Schedule first upgrade for upcoming Sunday
4. **Next**: Run `python3 redshift_upgrade.py` during window

## Notes

- No clear "zero activity" periods found - cluster is actively used 24/7
- Weekend early morning (01:00-04:00 UTC) shows consistently lowest activity
- Current 30-minute window may be too short for major version upgrades
- Consider 2-3 hour window for safety
