#!/usr/bin/env python3
"""
📈 PERFORMANCE ANALYTICS DASHBOARD - PHASE 3
============================================
Real-time dashboard for system performance, session health, and market intelligence.
Provides comprehensive visualization and monitoring capabilities.
"""

import asyncio
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, jsonify, request
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceAnalyticsDashboard:
    """Comprehensive performance analytics and monitoring dashboard"""
    
    def __init__(self):
        self.base_dir = Path.home() / ".macbid_scraper"
        self.health_db = self.base_dir / "session_health.db"
        self.intelligence_db = self.base_dir / "market_intelligence.db"
        self.breakdown_file = Path("breakdown.json")
        self.auth_config_file = Path("auth_config.json")
        
        # Dashboard data cache
        self.dashboard_data = {}
        self.last_update = None
        self.update_interval = 300  # 5 minutes
        
        # Flask app for web dashboard
        self.app = Flask(__name__)
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask routes for web dashboard"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
            
        @self.app.route('/api/health')
        def api_health():
            return jsonify(self.get_health_metrics())
            
        @self.app.route('/api/performance')
        def api_performance():
            return jsonify(self.get_performance_metrics())
            
        @self.app.route('/api/intelligence')
        def api_intelligence():
            return jsonify(self.get_intelligence_metrics())
            
        @self.app.route('/api/charts/health')
        def api_charts_health():
            return jsonify(self.generate_health_charts())
            
        @self.app.route('/api/charts/performance')
        def api_charts_performance():
            return jsonify(self.generate_performance_charts())
            
        @self.app.route('/api/realtime')
        def api_realtime():
            return jsonify(self.get_realtime_data())
            
    def get_health_metrics(self) -> Dict:
        """Get current session health metrics"""
        try:
            if not self.health_db.exists():
                return {'error': 'Health database not found'}
                
            with sqlite3.connect(self.health_db) as conn:
                # Latest health record
                cursor = conn.execute("""
                    SELECT * FROM session_health 
                    ORDER BY timestamp DESC LIMIT 1
                """)
                latest_health = cursor.fetchone()
                
                # Health summary (last 24 hours)
                cursor = conn.execute("""
                    SELECT 
                        AVG(health_score) as avg_health,
                        AVG(success_rate) as avg_success,
                        AVG(response_time) as avg_response,
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN health_score >= 70 THEN 1 ELSE 0 END) as healthy_checks
                    FROM session_health 
                    WHERE timestamp > datetime('now', '-24 hours')
                """)
                summary = cursor.fetchone()
                
                # Recent alerts
                cursor = conn.execute("""
                    SELECT alert_type, severity, COUNT(*) as count
                    FROM health_alerts 
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY alert_type, severity
                """)
                alerts = cursor.fetchall()
                
                if latest_health:
                    health_data = {
                        'current_health_score': latest_health[4] if latest_health[4] else 0,
                        'current_success_rate': latest_health[5] if latest_health[5] else 0,
                        'current_response_time': latest_health[6] if latest_health[6] else 0,
                        'current_status': latest_health[7] if latest_health[7] else 'UNKNOWN',
                        'last_update': latest_health[1] if latest_health[1] else '',
                        'session_id': latest_health[2][:20] + '...' if latest_health[2] else 'N/A'
                    }
                else:
                    health_data = {
                        'current_health_score': 0,
                        'current_success_rate': 0,
                        'current_response_time': 0,
                        'current_status': 'NO_DATA',
                        'last_update': '',
                        'session_id': 'N/A'
                    }
                    
                if summary and summary[0]:
                    health_data.update({
                        'avg_health_24h': summary[0],
                        'avg_success_24h': summary[1],
                        'avg_response_24h': summary[2],
                        'total_checks_24h': summary[3],
                        'uptime_percentage': (summary[4] / summary[3] * 100) if summary[3] > 0 else 0
                    })
                else:
                    health_data.update({
                        'avg_health_24h': 0,
                        'avg_success_24h': 0,
                        'avg_response_24h': 0,
                        'total_checks_24h': 0,
                        'uptime_percentage': 0
                    })
                    
                # Process alerts
                alert_summary = {}
                for alert in alerts:
                    alert_key = f"{alert[0]}_{alert[1]}"
                    alert_summary[alert_key] = alert[2]
                    
                health_data['alerts_24h'] = alert_summary
                
                return health_data
                
        except Exception as e:
            logger.error(f"❌ Error getting health metrics: {e}")
            return {'error': str(e)}
            
    def get_performance_metrics(self) -> Dict:
        """Get system performance metrics"""
        try:
            performance_data = {
                'system_status': 'operational',
                'last_session_capture': 'unknown',
                'total_requests_captured': 0,
                'capture_success_rate': 0,
                'average_execution_time': 0,
                'browser_sessions_active': 0
            }
            
            # Check breakdown file for latest capture data
            if self.breakdown_file.exists():
                with open(self.breakdown_file, 'r') as f:
                    breakdown_data = json.load(f)
                    
                performance_data['total_requests_captured'] = len(breakdown_data)
                
                # Calculate success rate from status codes
                successful_requests = 0
                total_with_status = 0
                
                for request_data in breakdown_data.values():
                    if isinstance(request_data, dict) and 'status_code' in request_data:
                        total_with_status += 1
                        if request_data['status_code'] < 400:
                            successful_requests += 1
                            
                if total_with_status > 0:
                    performance_data['capture_success_rate'] = (successful_requests / total_with_status) * 100
                    
            # Check auth config for session info
            if self.auth_config_file.exists():
                with open(self.auth_config_file, 'r') as f:
                    auth_data = json.load(f)
                    
                performance_data['last_session_capture'] = auth_data.get('timestamp', 'unknown')
                
            # Check intelligence database for processing metrics
            if self.intelligence_db.exists():
                with sqlite3.connect(self.intelligence_db) as conn:
                    cursor = conn.execute("""
                        SELECT AVG(processing_time), COUNT(*)
                        FROM processing_metrics 
                        WHERE timestamp > datetime('now', '-24 hours')
                    """)
                    processing_stats = cursor.fetchone()
                    
                    if processing_stats and processing_stats[0]:
                        performance_data['average_processing_time'] = processing_stats[0]
                        performance_data['processing_runs_24h'] = processing_stats[1]
                        
            return performance_data
            
        except Exception as e:
            logger.error(f"❌ Error getting performance metrics: {e}")
            return {'error': str(e)}
            
    def get_intelligence_metrics(self) -> Dict:
        """Get market intelligence metrics"""
        try:
            intelligence_data = {
                'opportunity_score': 0,
                'active_auctions': 0,
                'monitored_locations': [],
                'market_trends': {},
                'competition_level': 'unknown',
                'recommendations': []
            }
            
            if self.intelligence_db.exists():
                with sqlite3.connect(self.intelligence_db) as conn:
                    # Latest opportunity score
                    cursor = conn.execute("""
                        SELECT opportunity_score, insights
                        FROM auction_intelligence 
                        ORDER BY timestamp DESC LIMIT 1
                    """)
                    latest_intelligence = cursor.fetchone()
                    
                    if latest_intelligence:
                        intelligence_data['opportunity_score'] = latest_intelligence[0]
                        
                        # Parse insights for recommendations
                        try:
                            insights = json.loads(latest_intelligence[1])
                            intelligence_data['recommendations'] = insights.get('recommendations', [])
                        except:
                            pass
                            
                    # Market patterns summary
                    cursor = conn.execute("""
                        SELECT pattern_type, COUNT(*), AVG(confidence_score)
                        FROM market_patterns 
                        WHERE timestamp > datetime('now', '-24 hours')
                        GROUP BY pattern_type
                    """)
                    patterns = cursor.fetchall()
                    
                    pattern_summary = {}
                    for pattern in patterns:
                        pattern_summary[pattern[0]] = {
                            'count': pattern[1],
                            'avg_confidence': pattern[2]
                        }
                        
                    intelligence_data['market_patterns'] = pattern_summary
                    
            return intelligence_data
            
        except Exception as e:
            logger.error(f"❌ Error getting intelligence metrics: {e}")
            return {'error': str(e)}
            
    def generate_health_charts(self) -> Dict:
        """Generate health monitoring charts"""
        try:
            if not self.health_db.exists():
                return {'error': 'Health database not found'}
                
            with sqlite3.connect(self.health_db) as conn:
                # Health score over time
                df_health = pd.read_sql_query("""
                    SELECT timestamp, health_score, success_rate, response_time
                    FROM session_health 
                    WHERE timestamp > datetime('now', '-24 hours')
                    ORDER BY timestamp
                """, conn)
                
                charts = {}
                
                if not df_health.empty:
                    # Health score timeline
                    fig_health = px.line(
                        df_health, 
                        x='timestamp', 
                        y='health_score',
                        title='Session Health Score (24h)',
                        labels={'health_score': 'Health Score', 'timestamp': 'Time'}
                    )
                    fig_health.add_hline(y=70, line_dash="dash", line_color="orange", 
                                        annotation_text="Healthy Threshold")
                    charts['health_timeline'] = json.loads(json.dumps(fig_health, cls=PlotlyJSONEncoder))
                    
                    # Success rate chart
                    fig_success = px.line(
                        df_health, 
                        x='timestamp', 
                        y='success_rate',
                        title='Success Rate (24h)',
                        labels={'success_rate': 'Success Rate', 'timestamp': 'Time'}
                    )
                    charts['success_timeline'] = json.loads(json.dumps(fig_success, cls=PlotlyJSONEncoder))
                    
                    # Response time chart
                    fig_response = px.line(
                        df_health, 
                        x='timestamp', 
                        y='response_time',
                        title='Response Time (24h)',
                        labels={'response_time': 'Response Time (s)', 'timestamp': 'Time'}
                    )
                    charts['response_timeline'] = json.loads(json.dumps(fig_response, cls=PlotlyJSONEncoder))
                    
                # Alert distribution
                df_alerts = pd.read_sql_query("""
                    SELECT alert_type, severity, COUNT(*) as count
                    FROM health_alerts 
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY alert_type, severity
                """, conn)
                
                if not df_alerts.empty:
                    fig_alerts = px.bar(
                        df_alerts, 
                        x='alert_type', 
                        y='count',
                        color='severity',
                        title='Alert Distribution (24h)'
                    )
                    charts['alert_distribution'] = json.loads(json.dumps(fig_alerts, cls=PlotlyJSONEncoder))
                    
                return charts
                
        except Exception as e:
            logger.error(f"❌ Error generating health charts: {e}")
            return {'error': str(e)}
            
    def generate_performance_charts(self) -> Dict:
        """Generate performance monitoring charts"""
        try:
            charts = {}
            
            # Request capture analysis
            if self.breakdown_file.exists():
                with open(self.breakdown_file, 'r') as f:
                    breakdown_data = json.load(f)
                    
                # Endpoint frequency chart
                endpoint_counts = {}
                status_counts = {}
                
                for request_data in breakdown_data.values():
                    if isinstance(request_data, dict):
                        url = request_data.get('url', '')
                        status = request_data.get('status_code', 0)
                        
                        # Categorize endpoint
                        if 'analytics.google.com' in url:
                            endpoint = 'Google Analytics'
                        elif 'doubleclick.net' in url:
                            endpoint = 'DoubleClick'
                        elif 'facebook.com' in url:
                            endpoint = 'Facebook'
                        elif 'mac.bid' in url:
                            endpoint = 'Mac.bid'
                        else:
                            endpoint = 'Other'
                            
                        endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
                        
                        # Status code distribution
                        status_range = f"{status//100}xx" if status > 0 else 'Unknown'
                        status_counts[status_range] = status_counts.get(status_range, 0) + 1
                        
                # Endpoint distribution pie chart
                if endpoint_counts:
                    fig_endpoints = px.pie(
                        values=list(endpoint_counts.values()),
                        names=list(endpoint_counts.keys()),
                        title='Request Distribution by Endpoint'
                    )
                    charts['endpoint_distribution'] = json.loads(json.dumps(fig_endpoints, cls=PlotlyJSONEncoder))
                    
                # Status code distribution
                if status_counts:
                    fig_status = px.bar(
                        x=list(status_counts.keys()),
                        y=list(status_counts.values()),
                        title='HTTP Status Code Distribution'
                    )
                    charts['status_distribution'] = json.loads(json.dumps(fig_status, cls=PlotlyJSONEncoder))
                    
            return charts
            
        except Exception as e:
            logger.error(f"❌ Error generating performance charts: {e}")
            return {'error': str(e)}
            
    def get_realtime_data(self) -> Dict:
        """Get real-time dashboard data"""
        current_time = datetime.now()
        
        # Check if we need to update cached data
        if (self.last_update is None or 
            (current_time - self.last_update).total_seconds() > self.update_interval):
            
            self.dashboard_data = {
                'health': self.get_health_metrics(),
                'performance': self.get_performance_metrics(),
                'intelligence': self.get_intelligence_metrics(),
                'system_info': {
                    'last_update': current_time.isoformat(),
                    'update_interval': self.update_interval,
                    'dashboard_status': 'active'
                }
            }
            self.last_update = current_time
            
        return self.dashboard_data
        
    def generate_dashboard_summary(self) -> str:
        """Generate text-based dashboard summary"""
        data = self.get_realtime_data()
        
        summary = []
        summary.append("📈 PERFORMANCE ANALYTICS DASHBOARD")
        summary.append("=" * 50)
        summary.append("")
        
        # Health Summary
        health = data.get('health', {})
        summary.append("🔍 SESSION HEALTH")
        summary.append(f"   Current Health Score: {health.get('current_health_score', 0):.1f}/100")
        summary.append(f"   Success Rate: {health.get('current_success_rate', 0)*100:.1f}%")
        summary.append(f"   Response Time: {health.get('current_response_time', 0):.2f}s")
        summary.append(f"   Status: {health.get('current_status', 'UNKNOWN')}")
        summary.append(f"   24h Uptime: {health.get('uptime_percentage', 0):.1f}%")
        summary.append("")
        
        # Performance Summary
        performance = data.get('performance', {})
        summary.append("⚡ SYSTEM PERFORMANCE")
        summary.append(f"   Requests Captured: {performance.get('total_requests_captured', 0)}")
        summary.append(f"   Capture Success Rate: {performance.get('capture_success_rate', 0):.1f}%")
        summary.append(f"   Last Capture: {performance.get('last_session_capture', 'Unknown')}")
        summary.append("")
        
        # Intelligence Summary
        intelligence = data.get('intelligence', {})
        summary.append("🧠 MARKET INTELLIGENCE")
        summary.append(f"   Opportunity Score: {intelligence.get('opportunity_score', 0):.1f}/100")
        
        recommendations = intelligence.get('recommendations', [])
        if recommendations:
            summary.append("   Recommendations:")
            for rec in recommendations[:3]:  # Show top 3
                summary.append(f"     • {rec}")
        summary.append("")
        
        # System Status
        summary.append("🖥️ SYSTEM STATUS")
        health_score = health.get('current_health_score', 0)
        if health_score >= 80:
            summary.append("   🟢 SYSTEM HEALTHY - All systems operational")
        elif health_score >= 60:
            summary.append("   🟡 SYSTEM FAIR - Minor issues detected")
        else:
            summary.append("   🔴 SYSTEM CRITICAL - Immediate attention required")
            
        return "\n".join(summary)
        
    def start_web_dashboard(self, host='localhost', port=5000, debug=False):
        """Start the web-based dashboard"""
        logger.info(f"🌐 Starting web dashboard at http://{host}:{port}")
        
        # Create templates directory and basic template
        templates_dir = Path("templates")
        templates_dir.mkdir(exist_ok=True)
        
        dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Mac.bid Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric-card { 
            display: inline-block; 
            margin: 10px; 
            padding: 20px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            min-width: 200px;
        }
        .metric-value { font-size: 24px; font-weight: bold; }
        .metric-label { color: #666; }
        .chart-container { margin: 20px 0; }
    </style>
</head>
<body>
    <h1>📈 Mac.bid Performance Analytics Dashboard</h1>
    
    <div id="metrics"></div>
    <div id="charts"></div>
    
    <script>
        function updateDashboard() {
            fetch('/api/realtime')
                .then(response => response.json())
                .then(data => {
                    updateMetrics(data);
                });
                
            fetch('/api/charts/health')
                .then(response => response.json())
                .then(charts => {
                    updateCharts(charts);
                });
        }
        
        function updateMetrics(data) {
            const metricsDiv = document.getElementById('metrics');
            const health = data.health || {};
            const performance = data.performance || {};
            
            metricsDiv.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${(health.current_health_score || 0).toFixed(1)}/100</div>
                    <div class="metric-label">Health Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${((health.current_success_rate || 0) * 100).toFixed(1)}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${performance.total_requests_captured || 0}</div>
                    <div class="metric-label">Requests Captured</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${(health.uptime_percentage || 0).toFixed(1)}%</div>
                    <div class="metric-label">24h Uptime</div>
                </div>
            `;
        }
        
        function updateCharts(charts) {
            const chartsDiv = document.getElementById('charts');
            chartsDiv.innerHTML = '';
            
            Object.keys(charts).forEach(chartName => {
                if (charts[chartName] && !charts[chartName].error) {
                    const chartDiv = document.createElement('div');
                    chartDiv.id = chartName;
                    chartDiv.className = 'chart-container';
                    chartsDiv.appendChild(chartDiv);
                    
                    Plotly.newPlot(chartName, charts[chartName].data, charts[chartName].layout);
                }
            });
        }
        
        // Update dashboard every 30 seconds
        updateDashboard();
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
        """
        
        with open(templates_dir / "dashboard.html", "w") as f:
            f.write(dashboard_html)
            
        # Start Flask app
        self.app.run(host=host, port=port, debug=debug)

async def main():
    """Main function for performance analytics dashboard"""
    print("📈 PERFORMANCE ANALYTICS DASHBOARD - PHASE 3")
    print("=" * 60)
    
    dashboard = PerformanceAnalyticsDashboard()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "web":
            # Start web dashboard
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
            dashboard.start_web_dashboard(port=port)
            
        elif command == "summary":
            # Generate text summary
            summary = dashboard.generate_dashboard_summary()
            print(summary)
            
        elif command == "health":
            # Health metrics only
            health = dashboard.get_health_metrics()
            print(json.dumps(health, indent=2))
            
        elif command == "performance":
            # Performance metrics only
            performance = dashboard.get_performance_metrics()
            print(json.dumps(performance, indent=2))
            
        elif command == "intelligence":
            # Intelligence metrics only
            intelligence = dashboard.get_intelligence_metrics()
            print(json.dumps(intelligence, indent=2))
            
        else:
            print("Usage: python performance_analytics_dashboard.py [web|summary|health|performance|intelligence]")
            
    else:
        # Default: show summary
        summary = dashboard.generate_dashboard_summary()
        print(summary)

if __name__ == "__main__":
    import sys
    asyncio.run(main()) 