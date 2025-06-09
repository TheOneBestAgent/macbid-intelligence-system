#!/usr/bin/env python3
"""
📊 Firebase Cron Status Checker
Monitor the performance of the automated Firebase credential refresh system
"""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

def check_cron_status():
    """Check if cron job is installed and running"""
    print("🔄 FIREBASE CRON STATUS CHECKER")
    print("=" * 40)
    
    try:
        # Check if cron job is installed
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        
        if result.returncode == 0 and 'firebase_credential_monitor.py' in result.stdout:
            print("✅ Cron job is installed and active")
            
            # Count the number of scheduled jobs
            firebase_jobs = [line for line in result.stdout.split('\n') 
                           if 'firebase_credential_monitor.py' in line and not line.startswith('#')]
            print(f"   📅 {len(firebase_jobs)} scheduled credential checks:")
            
            for i, job in enumerate(firebase_jobs, 1):
                # Extract the schedule part
                schedule_part = job.split(' cd ')[0].strip()
                print(f"   {i}. {schedule_part}")
                
        else:
            print("❌ Cron job not found or not installed")
            return False
            
    except Exception as e:
        print(f"❌ Error checking cron status: {e}")
        return False
    
    return True

def check_log_file():
    """Check the cron log file for recent activity"""
    print(f"\n📋 CRON LOG ANALYSIS")
    print("=" * 25)
    
    log_file = Path("firebase_cron.log")
    
    if not log_file.exists():
        print("⚠️ Log file not found (firebase_cron.log)")
        print("   This is normal if cron hasn't run yet")
        return
    
    try:
        # Read the log file
        with open(log_file, 'r') as f:
            content = f.read()
        
        if not content.strip():
            print("📝 Log file exists but is empty")
            print("   Cron job hasn't run yet or no output generated")
            return
        
        # Analyze log content
        lines = content.strip().split('\n')
        print(f"📊 Log file contains {len(lines)} lines")
        
        # Look for recent activity (last 24 hours)
        recent_lines = []
        for line in lines[-20:]:  # Check last 20 lines
            if any(keyword in line for keyword in ['✅', '❌', '🔄', '📊']):
                recent_lines.append(line)
        
        if recent_lines:
            print(f"🕐 Recent activity (last {min(20, len(lines))} lines):")
            for line in recent_lines[-5:]:  # Show last 5 relevant lines
                print(f"   {line}")
        else:
            print("📝 No recent credential check activity found")
            
        # Check file size
        file_size = log_file.stat().st_size
        print(f"📁 Log file size: {file_size} bytes")
        
        # Check last modified time
        last_modified = datetime.fromtimestamp(log_file.stat().st_mtime)
        time_diff = datetime.now() - last_modified
        print(f"🕐 Last modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff} ago)")
        
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def check_firebase_credentials():
    """Test current Firebase credentials"""
    print(f"\n🧪 FIREBASE CREDENTIAL TEST")
    print("=" * 30)
    
    try:
        # Import and test credentials
        from firebase_credential_monitor import SimpleFirebaseCredentialMonitor
        
        monitor = SimpleFirebaseCredentialMonitor()
        
        # Get credential status
        status = monitor.get_credential_status()
        
        print(f"📊 Current Status:")
        print(f"   Firebase Session ID: {status['firebase_session_id']}")
        print(f"   SID: {status['sid']}")
        print(f"   Timestamp: {status['timestamp']}")
        
        # Test credentials
        is_valid = monitor.test_firebase_credentials()
        
        if is_valid:
            print("✅ Firebase credentials are working!")
        else:
            print("❌ Firebase credentials need refresh")
            
        return is_valid
        
    except Exception as e:
        print(f"❌ Error testing credentials: {e}")
        return False

def get_next_cron_runs():
    """Calculate when the next cron jobs will run"""
    print(f"\n⏰ NEXT SCHEDULED RUNS")
    print("=" * 25)
    
    now = datetime.now()
    
    # Calculate next 6-hour run (0, 6, 12, 18)
    current_hour = now.hour
    next_6hour_slots = [0, 6, 12, 18]
    
    next_6hour = None
    for slot in next_6hour_slots:
        if slot > current_hour:
            next_6hour = now.replace(hour=slot, minute=0, second=0, microsecond=0)
            break
    
    if not next_6hour:
        # Next day at midnight
        next_6hour = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate next business hour run (9-21, every 2 hours)
    business_hours = list(range(9, 22, 2))  # 9, 11, 13, 15, 17, 19, 21
    
    next_business = None
    for hour in business_hours:
        if hour > current_hour:
            next_business = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            break
    
    if not next_business:
        # Next day at 9 AM
        next_business = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    print(f"🕐 Next 6-hour check: {next_6hour.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   (in {next_6hour - now})")
    
    print(f"🕐 Next business hour check: {next_business.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   (in {next_business - now})")

def main():
    """Main status check function"""
    
    # Check cron installation
    cron_ok = check_cron_status()
    
    # Check log file
    check_log_file()
    
    # Test current credentials
    credentials_ok = check_firebase_credentials()
    
    # Show next scheduled runs
    get_next_cron_runs()
    
    # Summary
    print(f"\n📊 SYSTEM HEALTH SUMMARY")
    print("=" * 30)
    
    print(f"🔄 Cron Job: {'✅ Active' if cron_ok else '❌ Not Active'}")
    print(f"🔑 Credentials: {'✅ Working' if credentials_ok else '❌ Need Refresh'}")
    
    if cron_ok and credentials_ok:
        print(f"\n🎉 SYSTEM STATUS: ✅ FULLY OPERATIONAL")
        print("   Firebase credentials are being monitored automatically")
        print("   Real-time bid monitoring is ready for 24/7 operation")
    else:
        print(f"\n⚠️ SYSTEM STATUS: ❌ NEEDS ATTENTION")
        if not cron_ok:
            print("   - Set up cron job: crontab firebase_cron_setup.txt")
        if not credentials_ok:
            print("   - Run: python3 firebase_credential_monitor.py")

if __name__ == "__main__":
    main() 