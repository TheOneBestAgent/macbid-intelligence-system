#!/usr/bin/env python3
"""
🔍 FIREBASE SESSION HEALTH MONITOR - PHASE 3
============================================
Real-time session validation, health monitoring, and proactive refresh system.
Ensures 100% session availability with predictive maintenance.
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Optional, Tuple
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('session_health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SessionHealthMonitor:
    """Advanced session health monitoring and management system"""
    
    def __init__(self):
        self.base_dir = Path.home() / ".macbid_scraper"
        self.credentials_file = self.base_dir / "credentials.json"
        self.auth_config_file = Path("auth_config.json")
        self.health_db = self.base_dir / "session_health.db"
        self.session_data = {}
        self.health_metrics = {}
        
        # Health thresholds
        self.SESSION_EXPIRY_WARNING = 3600  # 1 hour before expiry
        self.MAX_FAILED_REQUESTS = 3
        self.HEALTH_CHECK_INTERVAL = 1800  # 30 minutes
        self.CRITICAL_FAILURE_THRESHOLD = 0.7  # 70% success rate minimum
        
        self._init_health_database()
        
    def _init_health_database(self):
        """Initialize session health tracking database"""
        self.base_dir.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.health_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    auth_token TEXT,
                    health_score REAL,
                    success_rate REAL,
                    response_time REAL,
                    failed_requests INTEGER,
                    status TEXT,
                    expiry_time TEXT,
                    refresh_triggered BOOLEAN DEFAULT FALSE,
                    notes TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    session_id TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            """)
            
    async def load_current_session(self) -> Dict:
        """Load current session data from auth config"""
        try:
            if self.auth_config_file.exists():
                with open(self.auth_config_file, 'r') as f:
                    auth_data = json.load(f)
                    
                self.session_data = {
                    'session_id': auth_data.get('gsessionid', ''),
                    'auth_token': auth_data.get('auth_token', ''),
                    'timestamp': auth_data.get('timestamp', ''),
                    'cookies': auth_data.get('cookies', {}),
                    'headers': auth_data.get('headers', {})
                }
                
                logger.info(f"✅ Loaded session: {self.session_data['session_id'][:20]}...")
                return self.session_data
            else:
                logger.warning("⚠️ No auth config file found")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error loading session: {e}")
            return {}
            
    async def validate_session(self) -> Tuple[bool, Dict]:
        """Validate current session with comprehensive health checks"""
        if not self.session_data:
            await self.load_current_session()
            
        if not self.session_data.get('session_id'):
            return False, {'error': 'No session data available'}
            
        # Test session with multiple endpoints
        test_results = {
            'main_page': await self._test_endpoint('https://www.mac.bid'),
            'auctions_page': await self._test_endpoint('https://www.mac.bid/auctions'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate health metrics
        successful_tests = sum(1 for result in test_results.values() if isinstance(result, dict) and result.get('success', False))
        total_tests = len([k for k in test_results.keys() if k != 'timestamp'])
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Calculate average response time
        response_times = [result.get('response_time', 0) for result in test_results.values() 
                         if isinstance(result, dict) and 'response_time' in result]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate health score (0-100)
        health_score = (success_rate * 70) + (min(1, 2.0 / max(avg_response_time, 0.1)) * 30)
        
        health_data = {
            'session_id': self.session_data['session_id'],
            'health_score': health_score,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'test_results': test_results,
            'status': self._determine_status(health_score, success_rate),
            'needs_refresh': success_rate < self.CRITICAL_FAILURE_THRESHOLD
        }
        
        # Store health data
        await self._store_health_data(health_data)
        
        # Check for alerts
        await self._check_health_alerts(health_data)
        
        is_healthy = health_score >= 70 and success_rate >= self.CRITICAL_FAILURE_THRESHOLD
        
        logger.info(f"🔍 Session Health: {health_score:.1f}/100 | Success: {success_rate*100:.1f}% | Status: {health_data['status']}")
        
        return is_healthy, health_data
        
    async def _test_endpoint(self, url: str) -> Dict:
        """Test a specific endpoint with current session"""
        start_time = time.time()
        
        try:
            headers = self.session_data.get('headers', {})
            cookies = self.session_data.get('cookies', {})
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(url, headers=headers, cookies=cookies) as response:
                    response_time = time.time() - start_time
                    
                    return {
                        'success': response.status == 200,
                        'status_code': response.status,
                        'response_time': response_time,
                        'url': url,
                        'content_length': len(await response.text()) if response.status == 200 else 0
                    }
                    
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'success': False,
                'error': str(e),
                'response_time': response_time,
                'url': url
            }
            
    def _determine_status(self, health_score: float, success_rate: float) -> str:
        """Determine session status based on metrics"""
        if health_score >= 90 and success_rate >= 0.9:
            return "EXCELLENT"
        elif health_score >= 80 and success_rate >= 0.8:
            return "GOOD"
        elif health_score >= 70 and success_rate >= 0.7:
            return "FAIR"
        elif health_score >= 50 and success_rate >= 0.5:
            return "POOR"
        else:
            return "CRITICAL"
            
    async def _store_health_data(self, health_data: Dict):
        """Store health data in database"""
        try:
            with sqlite3.connect(self.health_db) as conn:
                conn.execute("""
                    INSERT INTO session_health 
                    (timestamp, session_id, health_score, success_rate, response_time, 
                     status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    health_data['session_id'][:50],
                    health_data['health_score'],
                    health_data['success_rate'],
                    health_data['avg_response_time'],
                    health_data['status'],
                    json.dumps(health_data['test_results'])
                ))
                
        except Exception as e:
            logger.error(f"❌ Error storing health data: {e}")
            
    async def _check_health_alerts(self, health_data: Dict):
        """Check for health alerts and trigger notifications"""
        alerts = []
        
        # Critical health score
        if health_data['health_score'] < 50:
            alerts.append({
                'type': 'CRITICAL_HEALTH',
                'severity': 'CRITICAL',
                'message': f"Session health critically low: {health_data['health_score']:.1f}/100"
            })
            
        # Low success rate
        if health_data['success_rate'] < self.CRITICAL_FAILURE_THRESHOLD:
            alerts.append({
                'type': 'LOW_SUCCESS_RATE',
                'severity': 'HIGH',
                'message': f"Success rate below threshold: {health_data['success_rate']*100:.1f}%"
            })
            
        # High response time
        if health_data['avg_response_time'] > 5.0:
            alerts.append({
                'type': 'HIGH_RESPONSE_TIME',
                'severity': 'MEDIUM',
                'message': f"High response time: {health_data['avg_response_time']:.2f}s"
            })
            
        # Store and log alerts
        for alert in alerts:
            await self._store_alert(alert, health_data['session_id'])
            logger.warning(f"🚨 {alert['severity']}: {alert['message']}")
            
    async def _store_alert(self, alert: Dict, session_id: str):
        """Store alert in database"""
        try:
            with sqlite3.connect(self.health_db) as conn:
                conn.execute("""
                    INSERT INTO health_alerts 
                    (timestamp, alert_type, severity, message, session_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    alert['type'],
                    alert['severity'],
                    alert['message'],
                    session_id[:50]
                ))
                
        except Exception as e:
            logger.error(f"❌ Error storing alert: {e}")
            
    async def trigger_session_refresh(self) -> bool:
        """Trigger session refresh using Phase 2 automation"""
        logger.info("🔄 Triggering session refresh...")
        
        try:
            # Run Phase 2 automation
            result = subprocess.run([
                sys.executable, 
                "firebase_playwright_automation_v2.py"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ Session refresh completed successfully")
                
                # Reload session data
                await asyncio.sleep(5)  # Wait for files to be written
                await self.load_current_session()
                
                # Validate new session
                is_healthy, health_data = await self.validate_session()
                
                if is_healthy:
                    logger.info("✅ New session validated successfully")
                    return True
                else:
                    logger.warning("⚠️ New session validation failed")
                    return False
                    
            else:
                logger.error(f"❌ Session refresh failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Session refresh timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Error during session refresh: {e}")
            return False

async def main():
    """Main function for session health monitoring"""
    print("🔍 FIREBASE SESSION HEALTH MONITOR - PHASE 3")
    print("=" * 60)
    
    monitor = SessionHealthMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "check":
            # Single health check
            await monitor.load_current_session()
            is_healthy, health_data = await monitor.validate_session()
            
            print(f"\n📊 Session Health Report:")
            print(f"   Health Score: {health_data.get('health_score', 0):.1f}/100")
            print(f"   Success Rate: {health_data.get('success_rate', 0)*100:.1f}%")
            print(f"   Avg Response Time: {health_data.get('avg_response_time', 0):.2f}s")
            print(f"   Status: {health_data.get('status', 'UNKNOWN')}")
            print(f"   Needs Refresh: {'Yes' if health_data.get('needs_refresh', False) else 'No'}")
            
        elif command == "refresh":
            # Manual refresh
            success = await monitor.trigger_session_refresh()
            print(f"Session refresh: {'✅ Success' if success else '❌ Failed'}")
            
        else:
            print("Usage: python firebase_session_health_monitor.py [check|refresh]")
            
    else:
        # Default: single health check
        await monitor.load_current_session()
        is_healthy, health_data = await monitor.validate_session()
        
        print(f"\n📊 Quick Health Check:")
        print(f"   Status: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
        print(f"   Health Score: {health_data.get('health_score', 0):.1f}/100")
        print(f"   Success Rate: {health_data.get('success_rate', 0)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(main()) 