#!/usr/bin/env python3
"""
Quick Auction Scan - Periodic Opportunity Checker
Run this script periodically to check for new opportunities
"""

import subprocess
import sys
import time
from datetime import datetime

def run_quick_scan():
    """Run a quick auction scan"""
    print("🔍 QUICK AUCTION SCAN")
    print("=" * 50)
    print(f"⏰ Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Run the integrated system for a quick analysis
        result = subprocess.run([
            sys.executable, 
            "core_systems/integrated_auction_system.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Scan completed successfully!")
            
            # Extract key information from output
            lines = result.stdout.split('\n')
            
            # Find opportunity results
            in_results = False
            opportunities = []
            
            for line in lines:
                if "OPPORTUNITY ANALYSIS RESULTS:" in line:
                    in_results = True
                    continue
                elif "EXECUTING PORTFOLIO STRATEGY" in line:
                    in_results = False
                    break
                elif in_results and line.strip():
                    if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                        opportunities.append(line.strip())
                    elif "Opportunity Score:" in line:
                        opportunities.append(f"   {line.strip()}")
                    elif "Recommendation:" in line:
                        opportunities.append(f"   {line.strip()}")
                        opportunities.append("")  # Add spacing
            
            if opportunities:
                print("\n🎯 TOP OPPORTUNITIES:")
                print("-" * 40)
                for opp in opportunities[:15]:  # Show top 3 opportunities
                    print(opp)
            
            # Find portfolio results
            for line in lines:
                if "Total Investment:" in line:
                    print(f"\n💰 {line.strip()}")
                elif "Projected ROI:" in line:
                    print(f"📈 {line.strip()}")
                elif "TOP OPPORTUNITY:" in line:
                    print(f"\n🏆 {line.strip()}")
                    
        else:
            print("❌ Scan failed!")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Scan timed out (30 seconds)")
    except Exception as e:
        print(f"❌ Error during scan: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        # Continuous mode
        interval = 300  # 5 minutes
        if len(sys.argv) > 2:
            try:
                interval = int(sys.argv[2])
            except ValueError:
                print("Invalid interval, using 300 seconds")
        
        print(f"🔄 CONTINUOUS SCANNING MODE")
        print(f"⏱️  Scanning every {interval} seconds")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                run_quick_scan()
                print(f"\n⏰ Next scan in {interval} seconds...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Scanning stopped")
    else:
        # Single scan mode
        run_quick_scan()
        print("\n💡 TIP: Run 'python3 quick_scan.py --loop 300' for continuous scanning every 5 minutes")

if __name__ == "__main__":
    main() 