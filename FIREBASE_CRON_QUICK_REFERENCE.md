# 🔄 Firebase Cron Job - Quick Reference

## ✅ **SETUP COMPLETE!**

Your Firebase credential monitoring is now **FULLY AUTOMATED** with cron jobs running:

### 📅 **Scheduled Checks**
- **Every 6 hours**: 12 AM, 6 AM, 12 PM, 6 PM (main schedule)
- **Business hours**: 9 AM - 9 PM, every 2 hours (peak auction times)

### 🎯 **Current Status**
- ✅ **Cron Job**: Active and installed
- ✅ **Credentials**: Working (Status: 200)
- ✅ **Log File**: Created and logging properly
- ✅ **Next Check**: Automatically scheduled

## 🔧 **Quick Commands**

### Check System Status
```bash
python3 check_firebase_cron_status.py
```

### View Cron Jobs
```bash
crontab -l
```

### Check Recent Log Activity
```bash
tail -20 firebase_cron.log
```

### Manual Credential Check
```bash
python3 firebase_credential_monitor.py
```

### Test Firebase Connection
```bash
python3 firebase_realtime_bid_fixer.py
```

## 📊 **Monitoring Commands**

### Real-time Log Monitoring
```bash
tail -f firebase_cron.log
```

### Check Log File Size
```bash
ls -lh firebase_cron.log
```

### Count Successful Runs
```bash
grep "✅ Current credentials are working" firebase_cron.log | wc -l
```

### Check for Errors
```bash
grep "❌" firebase_cron.log
```

## 🛠️ **Management Commands**

### Disable Cron Job (if needed)
```bash
crontab -r
```

### Re-enable Cron Job
```bash
crontab firebase_cron_setup.txt
```

### Edit Cron Schedule
```bash
crontab -e
```

### Backup Cron Configuration
```bash
crontab -l > firebase_cron_backup.txt
```

## 🚨 **Troubleshooting**

### If Credentials Fail
```bash
# 1. Check current status
python3 check_firebase_cron_status.py

# 2. Manual refresh
python3 firebase_credential_monitor.py

# 3. Test Firebase connection
python3 firebase_realtime_bid_fixer.py
```

### If Cron Not Running
```bash
# Check if cron service is running (macOS)
sudo launchctl list | grep cron

# Check system logs for cron errors
grep cron /var/log/system.log
```

### Log File Issues
```bash
# Check permissions
ls -la firebase_cron.log

# Clear log file if too large
> firebase_cron.log

# Check disk space
df -h .
```

## 📈 **Success Indicators**

### ✅ **Everything Working When You See:**
- `✅ Cron job is installed and active`
- `✅ Credentials test PASSED (Status: 200)`
- `✅ Current credentials are working!`
- `🎉 SYSTEM STATUS: ✅ FULLY OPERATIONAL`

### ⚠️ **Needs Attention When You See:**
- `❌ Credentials test FAILED (Status: 400)`
- `❌ Cron job not found or not installed`
- `⚠️ Log file not found`
- `❌ SYSTEM STATUS: ❌ NEEDS ATTENTION`

## 🎯 **Next Scheduled Runs**

Your system will automatically check credentials at:
- **Next 6-hour check**: Every 6 hours starting from midnight
- **Next business check**: Every 2 hours from 9 AM to 9 PM

## 📞 **Emergency Recovery**

If everything fails:
1. **Manual credential update**: Edit `organized_system/core_systems/macbid_auth_config.py`
2. **Re-run setup**: `crontab firebase_cron_setup.txt`
3. **Test immediately**: `python3 firebase_credential_monitor.py`
4. **Verify Firebase**: `python3 firebase_realtime_bid_fixer.py`

## 🎉 **Success!**

Your Firebase credentials are now **automatically maintained** for uninterrupted real-time bid monitoring! 🚀

**The system will:**
- ✅ Check credentials every 6 hours
- ✅ Extra checks during business hours
- ✅ Automatically refresh when needed
- ✅ Log all activity for monitoring
- ✅ Keep your real-time monitoring running 24/7 