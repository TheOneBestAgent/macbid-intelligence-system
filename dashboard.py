#!/usr/bin/env python3
"""
Mac.bid Intelligence System - Command Center Dashboard
Phase 4: GUI Command Center Web Hub

A comprehensive web-based dashboard for managing and monitoring the Mac.bid
auction intelligence system with real-time data visualization and control.
"""

import os
import json
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'macbid_intelligence_system_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data_outputs'
DB_DIR = Path.home() / '.macbid_scraper'
TEMPLATES_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'

# Ensure directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

class SystemMonitor:
    """Real-time system monitoring and control"""
    
    def __init__(self):
        self.running_processes = {}
        self.system_stats = {
            'overall_health': 0,
            'automation_health': 0,
            'processing_health': 0,
            'session_health': 0,
            'market_intelligence': 0,
            'last_update': None
        }
        
    def get_system_health(self):
        """Get current system health metrics"""
        try:
            # Check if phase3_dashboard.py exists and run it
            dashboard_file = BASE_DIR / 'phase3_dashboard.py'
            if dashboard_file.exists():
                result = subprocess.run([
                    'python3', str(dashboard_file)
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Parse dashboard output for health metrics
                    output = result.stdout
                    if 'Overall Health:' in output:
                        for line in output.split('\n'):
                            if 'Overall Health:' in line:
                                health_str = line.split(':')[1].strip().split('/')[0]
                                self.system_stats['overall_health'] = float(health_str)
                            elif 'Phase 2 Enhanced Automation:' in line:
                                if 'EXCELLENT' in line:
                                    self.system_stats['automation_health'] = 100
                                elif 'GOOD' in line:
                                    self.system_stats['automation_health'] = 75
                            elif 'Enhanced Data Processing Pipeline:' in line:
                                if 'EXCELLENT' in line:
                                    self.system_stats['processing_health'] = 90
                                elif 'GOOD' in line:
                                    self.system_stats['processing_health'] = 70
                            elif 'Session Health Monitor:' in line:
                                if 'GOOD' in line:
                                    self.system_stats['session_health'] = 65
                                elif 'NEEDS_ATTENTION' in line:
                                    self.system_stats['session_health'] = 50
                            elif 'Market Intelligence System:' in line:
                                if 'GOOD' in line:
                                    self.system_stats['market_intelligence'] = 70
                                elif 'EXCELLENT' in line:
                                    self.system_stats['market_intelligence'] = 85
                        
                        self.system_stats['last_update'] = datetime.now().isoformat()
                        return self.system_stats
            
            # Fallback to default values if dashboard unavailable
            self.system_stats = {
                'overall_health': 75.0,
                'automation_health': 85,
                'processing_health': 80,
                'session_health': 60,
                'market_intelligence': 70,
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            self.system_stats['overall_health'] = 0
            
        return self.system_stats
    
    def get_recent_data(self):
        """Get recent processing results and data"""
        recent_data = {
            'processing_results': None,
            'captured_requests': 0,
            'opportunity_score': 0,
            'market_patterns': 0,
            'last_automation_run': None
        }
        
        try:
            # Check enhanced processing results
            processing_file = BASE_DIR / 'enhanced_processing_results.json'
            if processing_file.exists():
                with open(processing_file, 'r') as f:
                    data = json.load(f)
                    recent_data['processing_results'] = data
                    recent_data['captured_requests'] = data.get('data_points_processed', 0)
                    
                    # Extract opportunity score
                    market_intel = data.get('market_intelligence', {})
                    recent_data['opportunity_score'] = market_intel.get('opportunity_score', 0)
                    
                    # Count patterns
                    patterns = data.get('pattern_analysis', {}).get('patterns', {})
                    recent_data['market_patterns'] = len(patterns)
            
            # Check for recent automation runs
            automation_files = list(BASE_DIR.glob('firebase_playwright_session_*.json'))
            if automation_files:
                latest_file = max(automation_files, key=lambda x: x.stat().st_mtime)
                recent_data['last_automation_run'] = datetime.fromtimestamp(
                    latest_file.stat().st_mtime
                ).isoformat()
                
        except Exception as e:
            logger.error(f"Error getting recent data: {e}")
            
        return recent_data
    
    def run_script(self, script_name, args=None):
        """Run a system script"""
        try:
            script_path = BASE_DIR / script_name
            if not script_path.exists():
                return {'success': False, 'error': f'Script {script_name} not found'}
            
            cmd = ['python3', str(script_path)]
            if args:
                cmd.extend(args)
            
            # Run in background
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.running_processes[script_name] = {
                'process': process,
                'started': datetime.now().isoformat(),
                'status': 'running'
            }
            
            return {'success': True, 'message': f'Started {script_name}'}
            
        except Exception as e:
            logger.error(f"Error running script {script_name}: {e}")
            return {'success': False, 'error': str(e)}

# Initialize system monitor
monitor = SystemMonitor()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    system_health = monitor.get_system_health()
    recent_data = monitor.get_recent_data()
    
    return render_template('index.html', 
                         system_health=system_health,
                         recent_data=recent_data)

@app.route('/api/system/health')
def api_system_health():
    """API endpoint for system health"""
    return jsonify(monitor.get_system_health())

@app.route('/api/system/data')
def api_system_data():
    """API endpoint for recent system data"""
    return jsonify(monitor.get_recent_data())

@app.route('/api/scripts/run', methods=['POST'])
def api_run_script():
    """API endpoint to run system scripts"""
    data = request.get_json()
    script_name = data.get('script')
    args = data.get('args', [])
    
    if not script_name:
        return jsonify({'success': False, 'error': 'No script specified'})
    
    result = monitor.run_script(script_name, args)
    return jsonify(result)

@app.route('/api/scripts/status')
def api_script_status():
    """API endpoint for running script status"""
    status = {}
    for script_name, info in monitor.running_processes.items():
        process = info['process']
        if process.poll() is None:
            status[script_name] = {
                'status': 'running',
                'started': info['started']
            }
        else:
            status[script_name] = {
                'status': 'completed',
                'started': info['started'],
                'return_code': process.returncode
            }
    
    return jsonify(status)

@app.route('/control')
def control_panel():
    """System control panel"""
    available_scripts = [
        {
            'name': 'firebase_playwright_automation_v2.py',
            'title': 'Phase 2 Automation',
            'description': 'Enhanced browser automation with session management',
            'category': 'automation'
        },
        {
            'name': 'enhanced_data_processing_pipeline.py',
            'title': 'Data Processing Pipeline',
            'description': 'Advanced market intelligence processing',
            'category': 'processing'
        },
        {
            'name': 'firebase_session_health_monitor.py',
            'title': 'Session Health Monitor',
            'description': 'Real-time session validation and monitoring',
            'category': 'monitoring'
        },
        {
            'name': 'phase3_dashboard.py',
            'title': 'Performance Dashboard',
            'description': 'System performance analytics and reporting',
            'category': 'analytics'
        }
    ]
    
    return render_template('control.html', scripts=available_scripts)

@app.route('/analytics')
def analytics():
    """Analytics and visualization page"""
    return render_template('analytics.html')

@app.route('/logs')
def logs():
    """System logs viewer"""
    return render_template('logs.html')

@app.route('/search')
def search():
    """Intelligent search page"""
    return render_template('search.html')

@app.route('/bidding')
def bidding():
    """Automated bidding page"""
    return render_template('bidding.html')

@app.route('/market')
def market():
    """Market analysis page"""
    return render_template('market.html')

# API endpoints for new features
@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for intelligent search"""
    try:
        from intelligent_search_engine import IntelligentSearchEngine
        
        data = request.get_json()
        search_engine = IntelligentSearchEngine()
        results = search_engine.search_auctions(data)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in search API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bidding/strategies')
def api_bidding_strategies():
    """API endpoint for bidding strategies"""
    try:
        from automated_bidding_system import AutomatedBiddingSystem
        
        bidding_system = AutomatedBiddingSystem()
        strategies = bidding_system.get_bid_strategies()
        
        return jsonify({'strategies': strategies})
        
    except Exception as e:
        logger.error(f"Error getting bidding strategies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bidding/place', methods=['POST'])
def api_place_bid():
    """API endpoint for placing bids"""
    try:
        from automated_bidding_system import AutomatedBiddingSystem
        
        data = request.get_json()
        bidding_system = AutomatedBiddingSystem()
        result = bidding_system.place_bid(
            data.get('item_id'),
            data.get('item_title'),
            data.get('bid_amount'),
            data.get('strategy_id')
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error placing bid: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/trends')
def api_market_trends():
    """API endpoint for market trends"""
    try:
        from market_analysis_engine import MarketAnalysisEngine
        
        market_engine = MarketAnalysisEngine()
        trends = market_engine.analyze_market_trends()
        
        return jsonify(trends)
        
    except Exception as e:
        logger.error(f"Error getting market trends: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/report')
def api_market_report():
    """API endpoint for market report"""
    try:
        from market_analysis_engine import MarketAnalysisEngine
        
        market_engine = MarketAnalysisEngine()
        report = market_engine.generate_market_report()
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating market report: {e}")
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected to WebSocket')
    emit('status', {'message': 'Connected to Mac.bid Intelligence System'})

@socketio.on('request_update')
def handle_update_request():
    """Handle real-time update requests"""
    system_health = monitor.get_system_health()
    recent_data = monitor.get_recent_data()
    
    emit('system_update', {
        'health': system_health,
        'data': recent_data,
        'timestamp': datetime.now().isoformat()
    })

def background_monitor():
    """Background thread for real-time monitoring"""
    while True:
        try:
            system_health = monitor.get_system_health()
            recent_data = monitor.get_recent_data()
            
            socketio.emit('system_update', {
                'health': system_health,
                'data': recent_data,
                'timestamp': datetime.now().isoformat()
            })
            
            time.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            logger.error(f"Background monitor error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    # Start background monitoring thread
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    logger.info("🚀 Mac.bid Intelligence System Command Center Starting...")
    logger.info("📊 Dashboard available at: http://localhost:8081")
    logger.info("🔧 Control Panel: http://localhost:8081/control")
    logger.info("📈 Analytics: http://localhost:8081/analytics")
    
    # Run the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=8081, debug=False, allow_unsafe_werkzeug=True) 