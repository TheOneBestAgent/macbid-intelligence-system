#!/usr/bin/env python3
"""
Mac.bid Intelligence System - Dashboard Startup Script
Quick launcher for the GUI Command Center
"""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path

def main():
    print("🚀 Starting Mac.bid Intelligence System Command Center...")
    print("=" * 60)
    
    # Check if dashboard.py exists
    dashboard_path = Path(__file__).parent / 'dashboard.py'
    if not dashboard_path.exists():
        print("❌ Error: dashboard.py not found!")
        sys.exit(1)
    
    print("📊 Launching web dashboard...")
    print("🌐 Dashboard will be available at: http://localhost:8080")
    print("🔧 Control Panel: http://localhost:8080/control")
    print("📈 Analytics: http://localhost:8080/analytics")
    print("")
    print("💡 Features available:")
    print("   • Real-time system health monitoring")
    print("   • One-click script execution")
    print("   • Live market intelligence display")
    print("   • WebSocket-based real-time updates")
    print("   • Modern responsive UI")
    print("")
    print("⚡ Starting dashboard server...")
    
    try:
        # Start the dashboard
        process = subprocess.Popen([
            sys.executable, str(dashboard_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Open browser
        print("🌐 Opening browser...")
        webbrowser.open('http://localhost:8080')
        
        print("✅ Dashboard started successfully!")
        print("📝 Press Ctrl+C to stop the dashboard")
        print("")
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping dashboard...")
        process.terminate()
        print("✅ Dashboard stopped successfully!")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 