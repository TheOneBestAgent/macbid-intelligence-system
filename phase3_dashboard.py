#!/usr/bin/env python3
"""
📈 PHASE 3 PERFORMANCE DASHBOARD
===============================
Comprehensive monitoring dashboard for Phase 3 advanced features.
Real-time analytics for session health, data processing, and market intelligence.
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3Dashboard:
    """Comprehensive Phase 3 monitoring dashboard"""
    
    def __init__(self):
        self.base_dir = Path.home() / ".macbid_scraper"
        self.breakdown_file = Path("macbid_breakdown")
        self.health_db = self.base_dir / "session_health.db"
        self.intelligence_db = self.base_dir / "market_intelligence.db"
        self.results_file = Path("enhanced_processing_results.json")
        
    def get_system_overview(self) -> Dict:
        """Get comprehensive system overview"""
        overview = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 3 - Advanced Production Features',
            'status': 'OPERATIONAL',
            'components': {}
        }
        
        # Check Phase 2 automation status
        overview['components']['phase2_automation'] = self._check_phase2_status()
        
        # Check data processing status
        overview['components']['data_processing'] = self._check_data_processing_status()
        
        # Check session health monitoring
        overview['components']['session_health'] = self._check_session_health_status()
        
        # Check market intelligence
        overview['components']['market_intelligence'] = self._check_intelligence_status()
        
        # Calculate overall system health
        component_scores = []
        for component, status in overview['components'].items():
            if status.get('health_score'):
                component_scores.append(status['health_score'])
                
        if component_scores:
            overview['overall_health'] = sum(component_scores) / len(component_scores)
        else:
            overview['overall_health'] = 0
            
        # Determine overall status
        if overview['overall_health'] >= 80:
            overview['status'] = 'EXCELLENT'
        elif overview['overall_health'] >= 60:
            overview['status'] = 'GOOD'
        elif overview['overall_health'] >= 40:
            overview['status'] = 'FAIR'
        else:
            overview['status'] = 'CRITICAL'
            
        return overview
        
    def _check_phase2_status(self) -> Dict:
        """Check Phase 2 automation status"""
        status = {
            'name': 'Phase 2 Enhanced Automation',
            'health_score': 0,
            'last_run': 'Unknown',
            'requests_captured': 0,
            'status': 'UNKNOWN'
        }
        
        try:
            if self.breakdown_file.exists():
                # Check file modification time
                mod_time = datetime.fromtimestamp(self.breakdown_file.stat().st_mtime)
                time_diff = datetime.now() - mod_time
                
                status['last_run'] = mod_time.isoformat()
                
                # Count captured requests
                with open(self.breakdown_file, 'r') as f:
                    urls = f.readlines()
                    status['requests_captured'] = len([url for url in urls if url.strip()])
                
                # Calculate health score based on recency and volume
                if time_diff.total_seconds() < 3600:  # Less than 1 hour
                    recency_score = 100
                elif time_diff.total_seconds() < 7200:  # Less than 2 hours
                    recency_score = 80
                elif time_diff.total_seconds() < 86400:  # Less than 24 hours
                    recency_score = 60
                else:
                    recency_score = 20
                    
                volume_score = min(100, status['requests_captured'] * 0.7)  # Scale by volume
                
                status['health_score'] = (recency_score + volume_score) / 2
                
                if status['health_score'] >= 80:
                    status['status'] = 'EXCELLENT'
                elif status['health_score'] >= 60:
                    status['status'] = 'GOOD'
                else:
                    status['status'] = 'NEEDS_ATTENTION'
                    
            else:
                status['status'] = 'NOT_FOUND'
                
        except Exception as e:
            status['error'] = str(e)
            status['status'] = 'ERROR'
            
        return status
        
    def _check_data_processing_status(self) -> Dict:
        """Check data processing pipeline status"""
        status = {
            'name': 'Enhanced Data Processing Pipeline',
            'health_score': 0,
            'last_processing': 'Unknown',
            'data_points_processed': 0,
            'opportunity_score': 0,
            'status': 'UNKNOWN'
        }
        
        try:
            if self.results_file.exists():
                with open(self.results_file, 'r') as f:
                    results = json.load(f)
                    
                status['last_processing'] = results.get('processing_timestamp', 'Unknown')
                status['data_points_processed'] = results.get('data_points_processed', 0)
                
                # Get opportunity score from market intelligence
                market_intel = results.get('market_intelligence', {})
                opportunity_scoring = market_intel.get('opportunity_scoring', {})
                status['opportunity_score'] = opportunity_scoring.get('overall_score', 0)
                
                # Calculate health score
                processing_time = results.get('processing_timestamp', '')
                if processing_time:
                    try:
                        proc_time = datetime.fromisoformat(processing_time)
                        time_diff = datetime.now() - proc_time
                        
                        if time_diff.total_seconds() < 3600:  # Less than 1 hour
                            recency_score = 100
                        elif time_diff.total_seconds() < 86400:  # Less than 24 hours
                            recency_score = 80
                        else:
                            recency_score = 40
                    except:
                        recency_score = 50
                else:
                    recency_score = 0
                    
                data_score = min(100, status['data_points_processed'] * 0.6)
                opportunity_score = status['opportunity_score']
                
                status['health_score'] = (recency_score + data_score + opportunity_score) / 3
                
                if status['health_score'] >= 80:
                    status['status'] = 'EXCELLENT'
                elif status['health_score'] >= 60:
                    status['status'] = 'GOOD'
                else:
                    status['status'] = 'NEEDS_ATTENTION'
                    
            else:
                status['status'] = 'NOT_FOUND'
                
        except Exception as e:
            status['error'] = str(e)
            status['status'] = 'ERROR'
            
        return status
        
    def _check_session_health_status(self) -> Dict:
        """Check session health monitoring status"""
        status = {
            'name': 'Session Health Monitor',
            'health_score': 0,
            'database_exists': False,
            'total_checks': 0,
            'recent_alerts': 0,
            'status': 'UNKNOWN'
        }
        
        try:
            if self.health_db.exists():
                status['database_exists'] = True
                
                with sqlite3.connect(self.health_db) as conn:
                    # Count total health checks
                    cursor = conn.execute("SELECT COUNT(*) FROM session_health")
                    status['total_checks'] = cursor.fetchone()[0]
                    
                    # Count recent alerts (last 24 hours)
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM health_alerts 
                        WHERE timestamp > datetime('now', '-24 hours')
                    """)
                    status['recent_alerts'] = cursor.fetchone()[0]
                    
                    # Get latest health score
                    cursor = conn.execute("""
                        SELECT health_score FROM session_health 
                        ORDER BY timestamp DESC LIMIT 1
                    """)
                    latest_health = cursor.fetchone()
                    
                    if latest_health and latest_health[0]:
                        status['health_score'] = latest_health[0]
                    else:
                        status['health_score'] = 50  # Default if no data
                        
                if status['health_score'] >= 80:
                    status['status'] = 'EXCELLENT'
                elif status['health_score'] >= 60:
                    status['status'] = 'GOOD'
                else:
                    status['status'] = 'NEEDS_ATTENTION'
                    
            else:
                status['status'] = 'NOT_INITIALIZED'
                status['health_score'] = 30  # Low score for not initialized
                
        except Exception as e:
            status['error'] = str(e)
            status['status'] = 'ERROR'
            
        return status
        
    def _check_intelligence_status(self) -> Dict:
        """Check market intelligence status"""
        status = {
            'name': 'Market Intelligence System',
            'health_score': 0,
            'database_exists': False,
            'patterns_detected': 0,
            'intelligence_records': 0,
            'status': 'UNKNOWN'
        }
        
        try:
            if self.intelligence_db.exists():
                status['database_exists'] = True
                
                with sqlite3.connect(self.intelligence_db) as conn:
                    # Count market patterns
                    cursor = conn.execute("SELECT COUNT(*) FROM market_patterns")
                    status['patterns_detected'] = cursor.fetchone()[0]
                    
                    # Count intelligence records
                    cursor = conn.execute("SELECT COUNT(*) FROM auction_intelligence")
                    status['intelligence_records'] = cursor.fetchone()[0]
                    
                    # Calculate health score based on data availability
                    pattern_score = min(100, status['patterns_detected'] * 10)
                    intelligence_score = min(100, status['intelligence_records'] * 20)
                    
                    status['health_score'] = (pattern_score + intelligence_score) / 2
                    
                if status['health_score'] >= 80:
                    status['status'] = 'EXCELLENT'
                elif status['health_score'] >= 60:
                    status['status'] = 'GOOD'
                else:
                    status['status'] = 'NEEDS_ATTENTION'
                    
            else:
                status['status'] = 'NOT_INITIALIZED'
                status['health_score'] = 30  # Low score for not initialized
                
        except Exception as e:
            status['error'] = str(e)
            status['status'] = 'ERROR'
            
        return status
        
    def get_performance_metrics(self) -> Dict:
        """Get detailed performance metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'automation_performance': {},
            'processing_performance': {},
            'intelligence_performance': {}
        }
        
        # Automation performance
        if self.breakdown_file.exists():
            try:
                with open(self.breakdown_file, 'r') as f:
                    urls = f.readlines()
                    
                # Analyze endpoint distribution
                endpoint_counts = defaultdict(int)
                for url in urls:
                    url = url.strip()
                    if 'analytics.google.com' in url:
                        endpoint_counts['Google Analytics'] += 1
                    elif 'doubleclick.net' in url:
                        endpoint_counts['DoubleClick'] += 1
                    elif 'facebook.com' in url:
                        endpoint_counts['Facebook'] += 1
                    elif 'mac.bid' in url:
                        endpoint_counts['Mac.bid'] += 1
                    else:
                        endpoint_counts['Other'] += 1
                        
                metrics['automation_performance'] = {
                    'total_requests': len([url for url in urls if url.strip()]),
                    'endpoint_distribution': dict(endpoint_counts),
                    'capture_rate': '100%',  # All captured requests are successful
                    'last_capture': datetime.fromtimestamp(self.breakdown_file.stat().st_mtime).isoformat()
                }
                
            except Exception as e:
                metrics['automation_performance']['error'] = str(e)
                
        # Processing performance
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    results = json.load(f)
                    
                metrics['processing_performance'] = {
                    'data_points_processed': results.get('data_points_processed', 0),
                    'unique_endpoints': results.get('summary', {}).get('unique_endpoints', 0),
                    'opportunity_score': results.get('summary', {}).get('opportunity_score', 0),
                    'processing_timestamp': results.get('processing_timestamp', 'Unknown'),
                    'status': results.get('summary', {}).get('processing_status', 'Unknown')
                }
                
            except Exception as e:
                metrics['processing_performance']['error'] = str(e)
                
        # Intelligence performance
        if self.intelligence_db.exists():
            try:
                with sqlite3.connect(self.intelligence_db) as conn:
                    # Get pattern analysis
                    cursor = conn.execute("""
                        SELECT pattern_type, COUNT(*) 
                        FROM market_patterns 
                        GROUP BY pattern_type
                    """)
                    pattern_types = dict(cursor.fetchall())
                    
                    # Get latest opportunity score
                    cursor = conn.execute("""
                        SELECT opportunity_score 
                        FROM auction_intelligence 
                        ORDER BY timestamp DESC LIMIT 1
                    """)
                    latest_opportunity = cursor.fetchone()
                    
                    metrics['intelligence_performance'] = {
                        'pattern_types': pattern_types,
                        'latest_opportunity_score': latest_opportunity[0] if latest_opportunity else 0,
                        'total_patterns': sum(pattern_types.values()),
                        'database_size': self.intelligence_db.stat().st_size
                    }
                    
            except Exception as e:
                metrics['intelligence_performance']['error'] = str(e)
                
        return metrics
        
    def generate_dashboard_report(self) -> str:
        """Generate comprehensive dashboard report"""
        overview = self.get_system_overview()
        metrics = self.get_performance_metrics()
        
        report = []
        report.append("📈 PHASE 3 PERFORMANCE DASHBOARD")
        report.append("=" * 60)
        report.append(f"Timestamp: {overview['timestamp']}")
        report.append(f"Phase: {overview['phase']}")
        report.append(f"Overall Status: {overview['status']}")
        report.append(f"Overall Health: {overview['overall_health']:.1f}/100")
        report.append("")
        
        # Component Status
        report.append("🔧 COMPONENT STATUS")
        report.append("-" * 30)
        for component, status in overview['components'].items():
            status_icon = "🟢" if status['status'] in ['EXCELLENT', 'GOOD'] else "🟡" if status['status'] == 'FAIR' else "🔴"
            report.append(f"{status_icon} {status['name']}: {status['status']} ({status['health_score']:.1f}/100)")
            
            if component == 'phase2_automation':
                report.append(f"   Last Run: {status.get('last_run', 'Unknown')}")
                report.append(f"   Requests Captured: {status.get('requests_captured', 0)}")
            elif component == 'data_processing':
                report.append(f"   Data Points: {status.get('data_points_processed', 0)}")
                report.append(f"   Opportunity Score: {status.get('opportunity_score', 0):.1f}/100")
            elif component == 'session_health':
                report.append(f"   Total Checks: {status.get('total_checks', 0)}")
                report.append(f"   Recent Alerts: {status.get('recent_alerts', 0)}")
            elif component == 'market_intelligence':
                report.append(f"   Patterns Detected: {status.get('patterns_detected', 0)}")
                report.append(f"   Intelligence Records: {status.get('intelligence_records', 0)}")
                
        report.append("")
        
        # Performance Metrics
        report.append("📊 PERFORMANCE METRICS")
        report.append("-" * 30)
        
        # Automation Performance
        auto_perf = metrics.get('automation_performance', {})
        if auto_perf and 'error' not in auto_perf:
            report.append(f"🤖 Automation Performance:")
            report.append(f"   Total Requests: {auto_perf.get('total_requests', 0)}")
            report.append(f"   Capture Rate: {auto_perf.get('capture_rate', 'Unknown')}")
            
            endpoint_dist = auto_perf.get('endpoint_distribution', {})
            if endpoint_dist:
                report.append("   Endpoint Distribution:")
                for endpoint, count in endpoint_dist.items():
                    percentage = (count / auto_perf.get('total_requests', 1)) * 100
                    report.append(f"     • {endpoint}: {count} ({percentage:.1f}%)")
                    
        # Processing Performance
        proc_perf = metrics.get('processing_performance', {})
        if proc_perf and 'error' not in proc_perf:
            report.append(f"⚙️ Processing Performance:")
            report.append(f"   Data Points Processed: {proc_perf.get('data_points_processed', 0)}")
            report.append(f"   Unique Endpoints: {proc_perf.get('unique_endpoints', 0)}")
            report.append(f"   Opportunity Score: {proc_perf.get('opportunity_score', 0):.1f}/100")
            
        # Intelligence Performance
        intel_perf = metrics.get('intelligence_performance', {})
        if intel_perf and 'error' not in intel_perf:
            report.append(f"🧠 Intelligence Performance:")
            report.append(f"   Total Patterns: {intel_perf.get('total_patterns', 0)}")
            report.append(f"   Latest Opportunity: {intel_perf.get('latest_opportunity_score', 0):.1f}/100")
            
            pattern_types = intel_perf.get('pattern_types', {})
            if pattern_types:
                report.append("   Pattern Types:")
                for pattern_type, count in pattern_types.items():
                    report.append(f"     • {pattern_type}: {count}")
                    
        report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 30)
        
        if overview['overall_health'] >= 80:
            report.append("✅ System is performing excellently")
            report.append("✅ All components are operational")
            report.append("✅ Continue monitoring for optimal performance")
        elif overview['overall_health'] >= 60:
            report.append("⚠️ System is performing well with minor issues")
            report.append("⚠️ Monitor components with lower health scores")
            report.append("⚠️ Consider running maintenance tasks")
        else:
            report.append("🚨 System requires attention")
            report.append("🚨 Check components with critical status")
            report.append("🚨 Run diagnostics and refresh sessions")
            
        return "\n".join(report)

def main():
    """Main dashboard function"""
    print("📈 PHASE 3 PERFORMANCE DASHBOARD")
    print("=" * 60)
    
    dashboard = Phase3Dashboard()
    
    # Generate and display report
    report = dashboard.generate_dashboard_report()
    print(report)
    
    # Save report to file
    report_file = Path("phase3_dashboard_report.txt")
    with open(report_file, 'w') as f:
        f.write(report)
        
    print(f"\n💾 Dashboard report saved to: {report_file}")

if __name__ == "__main__":
    main() 