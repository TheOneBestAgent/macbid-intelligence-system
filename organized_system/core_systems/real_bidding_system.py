#!/usr/bin/env python3
"""
Real Bidding System for Mac.bid
Combines API-based bidding with browser automation fallback
"""

import asyncio
import aiohttp
import json
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import os

@dataclass
class BidRequest:
    lot_id: int
    auction_id: int
    bid_amount: float
    max_bid: float
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    timing_strategy: str = "IMMEDIATE"  # IMMEDIATE, LAST_MINUTE, SNIPE
    customer_id: int = 2710619
    notes: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class BidResult:
    success: bool
    lot_id: int
    bid_amount: float
    timestamp: str
    method: str  # API, BROWSER, FAILED
    message: str
    response_data: Optional[Dict] = None
    error: Optional[str] = None
    execution_time: float = 0.0

class RealBiddingSystem:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.base_url = "https://www.mac.bid"
        self.customer_id = 2710619
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data_outputs/real_bidding_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Session configuration
        self.session_headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.6',
            'content-type': 'application/json',
            'origin': 'https://www.mac.bid',
            'referer': 'https://www.mac.bid/',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        
        self.session_cookies = {
            '__stripe_mid': 'b1219cc5-9a1f-4e9b-9b3b-ce16a3d90ba32b7fa4',
            'CookieConsent': 'true',
            'ab.storage.deviceId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A6557c69b-3239-8d82-7b30-ec5862a4de57%7Ce%3Aundefined%7Cc%3A1747345668914%7Cl%3A1749267987617',
            'ab.storage.userId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A2710619%7Ce%3Aundefined%7Cc%3A1749188938629%7Cl%3A1749267987617',
            '__stripe_sid': '82edccd6-9b05-4a36-a118-e155bd9212b7ec69fb',
            'mp_78faade7af6b4f2ee5e1af36d8ac6232_mixpanel': '%7B%22distinct_id%22%3A%202710619%2C%22%24device_id%22%3A%20%22196d5eae0323e9-06ed80c653d2808-19525636-13c680-196d5eae0323e9%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22platform%22%3A%20%22website%22%2C%22selected_locations%22%3A%20%5B%0A%20%20%20%20%22Rock%20Hill%22%2C%0A%20%20%20%20%22Gastonia%22%0A%5D%2C%22%24user_id%22%3A%202710619%2C%22active_items%22%3A%20%5B%0A%20%20%20%20%7B%22id%22%3A%2046608657%2C%22invoice_id%22%3A%2018714030%2C%22box_size%22%3A%20%22large%22%2C%22warehouse_location%22%3A%20%22ANL-D-BIN-55%22%2C%22removal_container%22%3A%20null%2C%22product_name%22%3A%20%22KOKISO%20metal%20%22%2C%22status%22%3A%20%22PENDING-TRANSFER%22%2C%22boxes%22%3A%201%2C%22note%22%3A%20null%2C%22current_location_id%22%3A%2038%2C%22allow_transfers%22%3A%201%2C%22allow_shipping%22%3A%200%2C%22is_turbo%22%3A%200%2C%22free_transfers%22%3A%200%2C%22auction_number%22%3A%20%22ANL2506-05-A2%22%2C%22auction_abandon_date%22%3A%20%222025-06-10T18%3A00%3A00.000Z%22%2C%22abandon_date%22%3A%20null%2C%22lot_number%22%3A%20%221726Z%22%2C%22lot_id%22%3A%2035490378%2C%22has_buyer_assurance%22%3A%200%2C%22item_price%22%3A%205.67%2C%22cover_image%22%3A%20%22https%3A%2F%2Fm.media-amazon.com%2Fimages%2FI%2F71fm%2BEdRyKL.jpg%22%2C%22grand_total%22%3A%205.67%2C%22date_paid%22%3A%20%222025-06-06T09%3A20%3A50.000Z%22%2C%22transfer_id%22%3A%206229971%2C%22start_location_code%22%3A%20%22ANL%22%2C%22dest_location_code%22%3A%20%22RHA%22%2C%22start_location_id%22%3A%2038%2C%22dest_location_id%22%3A%2028%2C%22grouping_id%22%3A%20%2218714030_200_35872237%22%2C%22auction_lot_deadline%22%3A%20null%7D%0A%5D%2C%22mac_bucks_balance%22%3A%200%2C%22mac_bucks_gift_balance%22%3A%200%2C%22active_membership%22%3A%20%7B%22id%22%3A%20123339%2C%22date_created%22%3A%20%222025-05-29T18%3A11%3A59.000Z%22%2C%22membership_plan%22%3A%20%22STANDARD%22%2C%22customer_id%22%3A%202710619%2C%22bill_period%22%3A%20%22MONTHLY%22%2C%22bill_amount%22%3A%209.99%2C%22date_cancelled%22%3A%20null%2C%22external_id%22%3A%20%22sub_1RUFc8DhtPPAHVyel4iCCWV7%22%2C%22cancel_reason%22%3A%20null%2C%22stripe_customer_id%22%3A%20%22cus_S6Y0gK006usyW7%22%2C%22date_updated%22%3A%20null%7D%2C%22watchlist_count%22%3A%207%2C%22onboarding%22%3A%20true%7D',
            'ab.storage.sessionId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3Aa18c4004-ac5d-06ae-84af-39127b94f2a6%7Ce%3A1749269831396%7Cc%3A1749267987616%7Cl%3A1749268031396'
        }
        
        # Initialize database
        self.init_database()
        
        # Bidding statistics
        self.session_stats = {
            'session_start': datetime.now().isoformat(),
            'bids_attempted': 0,
            'bids_successful': 0,
            'bids_failed': 0,
            'total_amount_bid': 0.0,
            'api_attempts': 0,
            'browser_attempts': 0
        }
    
    def init_database(self):
        """Initialize SQLite database for bid tracking"""
        os.makedirs('databases', exist_ok=True)
        
        self.conn = sqlite3.connect('databases/real_bidding_system.db')
        cursor = self.conn.cursor()
        
        # Create bid requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER NOT NULL,
                auction_id INTEGER NOT NULL,
                bid_amount REAL NOT NULL,
                max_bid REAL NOT NULL,
                priority TEXT NOT NULL,
                timing_strategy TEXT NOT NULL,
                customer_id INTEGER NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        ''')
        
        # Create bid results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                lot_id INTEGER NOT NULL,
                bid_amount REAL NOT NULL,
                success BOOLEAN NOT NULL,
                method TEXT NOT NULL,
                message TEXT,
                response_data TEXT,
                error TEXT,
                execution_time REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (request_id) REFERENCES bid_requests (id)
            )
        ''')
        
        # Create discovered endpoints table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovered_endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER,
                response_time REAL,
                success_rate REAL DEFAULT 0.0,
                last_tested TEXT,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        self.conn.commit()
        self.logger.info("✅ Database initialized")
    
    async def discover_bidding_endpoints(self) -> List[Dict]:
        """Discover and test potential bidding endpoints"""
        
        self.logger.info("🔍 Discovering bidding endpoints...")
        
        # Potential bidding endpoints based on common patterns
        potential_endpoints = [
            # Next.js API routes (most likely)
            {"endpoint": "/api/bid", "method": "POST"},
            {"endpoint": "/api/bids", "method": "POST"},
            {"endpoint": "/api/place-bid", "method": "POST"},
            {"endpoint": "/api/auction/bid", "method": "POST"},
            {"endpoint": "/api/lot/bid", "method": "POST"},
            
            # RESTful patterns
            {"endpoint": f"/api/lots/{35863830}/bids", "method": "POST"},
            {"endpoint": f"/api/auctions/{48796}/bids", "method": "POST"},
            
            # GraphQL
            {"endpoint": "/graphql", "method": "POST"},
            {"endpoint": "/api/graphql", "method": "POST"},
        ]
        
        working_endpoints = []
        
        async with aiohttp.ClientSession(
            headers=self.session_headers,
            cookies=self.session_cookies,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            
            for endpoint_info in potential_endpoints:
                endpoint = endpoint_info["endpoint"]
                method = endpoint_info["method"]
                
                try:
                    start_time = time.time()
                    
                    # Test with sample bid data
                    test_data = {
                        "lot_id": 35863830,
                        "auction_id": 48796,
                        "bid_amount": 1.00,
                        "customer_id": self.customer_id
                    }
                    
                    if endpoint.endswith("/graphql"):
                        # GraphQL mutation test
                        test_data = {
                            "query": "mutation { placeBid(lotId: 35863830, amount: 1.00) { success message } }"
                        }
                    
                    url = f"{self.base_url}{endpoint}"
                    
                    if method == "POST":
                        async with session.post(url, json=test_data) as response:
                            response_time = time.time() - start_time
                            
                            # Log the attempt
                            self.log_endpoint_test(endpoint, method, response.status, response_time)
                            
                            # Check if this looks like a working endpoint
                            if response.status in [200, 201, 202]:
                                response_text = await response.text()
                                working_endpoints.append({
                                    "endpoint": endpoint,
                                    "method": method,
                                    "status_code": response.status,
                                    "response_time": response_time,
                                    "response_preview": response_text[:200]
                                })
                                self.logger.info(f"✅ Found working endpoint: {method} {endpoint} ({response.status})")
                            
                            elif response.status in [400, 422]:
                                # These might be validation errors, which means the endpoint exists
                                response_text = await response.text()
                                working_endpoints.append({
                                    "endpoint": endpoint,
                                    "method": method,
                                    "status_code": response.status,
                                    "response_time": response_time,
                                    "response_preview": response_text[:200],
                                    "note": "Validation error - endpoint exists but needs correct data"
                                })
                                self.logger.info(f"⚠️  Validation error endpoint: {method} {endpoint} ({response.status})")
                
                except Exception as e:
                    self.logger.debug(f"❌ {method} {endpoint}: {str(e)}")
                
                # Small delay between tests
                await asyncio.sleep(0.5)
        
        self.logger.info(f"🔍 Discovery complete. Found {len(working_endpoints)} potential endpoints")
        return working_endpoints
    
    def log_endpoint_test(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Log endpoint test results to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO discovered_endpoints 
            (endpoint, method, status_code, response_time, last_tested)
            VALUES (?, ?, ?, ?, ?)
        ''', (endpoint, method, status_code, response_time, datetime.now().isoformat()))
        self.conn.commit()
    
    async def attempt_api_bid(self, bid_request: BidRequest) -> BidResult:
        """Attempt to place bid using API endpoints"""
        
        start_time = time.time()
        self.session_stats['api_attempts'] += 1
        
        self.logger.info(f"🎯 Attempting API bid: ${bid_request.bid_amount} on lot {bid_request.lot_id}")
        
        if self.dry_run:
            execution_time = time.time() - start_time
            return BidResult(
                success=True,
                lot_id=bid_request.lot_id,
                bid_amount=bid_request.bid_amount,
                timestamp=datetime.now().isoformat(),
                method="API_DRY_RUN",
                message="DRY RUN: API bid would have been attempted",
                execution_time=execution_time
            )
        
        # Get working endpoints from database
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT endpoint, method FROM discovered_endpoints 
            WHERE is_active = 1 AND status_code IN (200, 201, 202, 400, 422)
            ORDER BY success_rate DESC, response_time ASC
        ''')
        
        endpoints = cursor.fetchall()
        
        if not endpoints:
            # Discover endpoints first
            discovered = await self.discover_bidding_endpoints()
            if discovered:
                endpoints = [(ep["endpoint"], ep["method"]) for ep in discovered]
        
        # Try each endpoint
        async with aiohttp.ClientSession(
            headers=self.session_headers,
            cookies=self.session_cookies,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:
            
            for endpoint, method in endpoints:
                try:
                    # Prepare bid data
                    bid_data = {
                        "lot_id": bid_request.lot_id,
                        "auction_id": bid_request.auction_id,
                        "bid_amount": bid_request.bid_amount,
                        "customer_id": bid_request.customer_id,
                        "max_bid": bid_request.max_bid
                    }
                    
                    if endpoint.endswith("/graphql"):
                        # GraphQL mutation
                        bid_data = {
                            "query": f"""
                            mutation {{
                                placeBid(
                                    lotId: {bid_request.lot_id},
                                    amount: {bid_request.bid_amount},
                                    customerId: {bid_request.customer_id}
                                ) {{
                                    success
                                    message
                                    bidId
                                }}
                            }}
                            """
                        }
                    
                    url = f"{self.base_url}{endpoint}"
                    
                    async with session.post(url, json=bid_data) as response:
                        response_text = await response.text()
                        execution_time = time.time() - start_time
                        
                        if response.status in [200, 201, 202]:
                            try:
                                response_data = await response.json()
                            except:
                                response_data = {"raw_response": response_text}
                            
                            # Check if bid was actually successful
                            success_indicators = ["success", "placed", "confirmed", "accepted"]
                            is_successful = any(indicator in response_text.lower() for indicator in success_indicators)
                            
                            if is_successful:
                                self.session_stats['bids_successful'] += 1
                                self.session_stats['total_amount_bid'] += bid_request.bid_amount
                                
                                return BidResult(
                                    success=True,
                                    lot_id=bid_request.lot_id,
                                    bid_amount=bid_request.bid_amount,
                                    timestamp=datetime.now().isoformat(),
                                    method="API",
                                    message=f"Bid placed successfully via {endpoint}",
                                    response_data=response_data,
                                    execution_time=execution_time
                                )
                        
                        # Log the attempt for learning
                        self.logger.debug(f"API attempt {endpoint}: {response.status} - {response_text[:100]}")
                
                except Exception as e:
                    self.logger.debug(f"API error {endpoint}: {str(e)}")
                    continue
        
        execution_time = time.time() - start_time
        return BidResult(
            success=False,
            lot_id=bid_request.lot_id,
            bid_amount=bid_request.bid_amount,
            timestamp=datetime.now().isoformat(),
            method="API_FAILED",
            message="All API endpoints failed",
            error="No working API endpoints found",
            execution_time=execution_time
        )
    
    def attempt_browser_bid(self, bid_request: BidRequest) -> BidResult:
        """Attempt to place bid using browser automation (fallback)"""
        
        start_time = time.time()
        self.session_stats['browser_attempts'] += 1
        
        self.logger.info(f"🌐 Attempting browser bid: ${bid_request.bid_amount} on lot {bid_request.lot_id}")
        
        if self.dry_run:
            execution_time = time.time() - start_time
            return BidResult(
                success=True,
                lot_id=bid_request.lot_id,
                bid_amount=bid_request.bid_amount,
                timestamp=datetime.now().isoformat(),
                method="BROWSER_DRY_RUN",
                message="DRY RUN: Browser bid would have been attempted",
                execution_time=execution_time
            )
        
        # For now, return a placeholder - browser automation would be implemented here
        # This would use the BrowserBiddingAutomation class we created earlier
        execution_time = time.time() - start_time
        
        return BidResult(
            success=False,
            lot_id=bid_request.lot_id,
            bid_amount=bid_request.bid_amount,
            timestamp=datetime.now().isoformat(),
            method="BROWSER_NOT_IMPLEMENTED",
            message="Browser automation not yet implemented in this version",
            error="Browser fallback needs implementation",
            execution_time=execution_time
        )
    
    async def place_bid(self, bid_request: BidRequest) -> BidResult:
        """Place a bid using the best available method"""
        
        self.session_stats['bids_attempted'] += 1
        
        # Store bid request in database
        request_id = self.store_bid_request(bid_request)
        
        self.logger.info(f"🎯 Placing bid: ${bid_request.bid_amount} on lot {bid_request.lot_id}")
        
        # Try API first (faster and more reliable)
        api_result = await self.attempt_api_bid(bid_request)
        
        if api_result.success:
            # Store successful result
            self.store_bid_result(request_id, api_result)
            return api_result
        
        # Fallback to browser automation
        self.logger.info("🔄 API failed, falling back to browser automation...")
        browser_result = self.attempt_browser_bid(bid_request)
        
        # Store result
        self.store_bid_result(request_id, browser_result)
        
        if not browser_result.success:
            self.session_stats['bids_failed'] += 1
        
        return browser_result
    
    def store_bid_request(self, bid_request: BidRequest) -> int:
        """Store bid request in database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO bid_requests 
            (lot_id, auction_id, bid_amount, max_bid, priority, timing_strategy, customer_id, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bid_request.lot_id,
            bid_request.auction_id,
            bid_request.bid_amount,
            bid_request.max_bid,
            bid_request.priority,
            bid_request.timing_strategy,
            bid_request.customer_id,
            bid_request.notes,
            bid_request.created_at
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def store_bid_result(self, request_id: int, result: BidResult):
        """Store bid result in database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO bid_results 
            (request_id, lot_id, bid_amount, success, method, message, response_data, error, execution_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request_id,
            result.lot_id,
            result.bid_amount,
            result.success,
            result.method,
            result.message,
            json.dumps(result.response_data) if result.response_data else None,
            result.error,
            result.execution_time,
            result.timestamp
        ))
        self.conn.commit()
    
    async def execute_bidding_queue(self, bid_requests: List[BidRequest]) -> List[BidResult]:
        """Execute multiple bids with intelligent timing"""
        
        self.logger.info(f"🎯 Executing bidding queue: {len(bid_requests)} bids")
        
        results = []
        
        # Sort by priority and timing strategy
        sorted_requests = sorted(bid_requests, key=lambda x: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x.priority],
            {"SNIPE": 0, "LAST_MINUTE": 1, "IMMEDIATE": 2}[x.timing_strategy]
        ))
        
        for i, bid_request in enumerate(sorted_requests):
            self.logger.info(f"Processing bid {i+1}/{len(sorted_requests)}")
            
            # Execute bid
            result = await self.place_bid(bid_request)
            results.append(result)
            
            # Log result
            if result.success:
                self.logger.info(f"✅ Bid successful: ${result.bid_amount} on lot {result.lot_id} via {result.method}")
            else:
                self.logger.error(f"❌ Bid failed: {result.message}")
            
            # Wait between bids to avoid rate limiting
            await asyncio.sleep(1)
        
        # Generate session report
        self.generate_session_report(results)
        
        return results
    
    def generate_session_report(self, results: List[BidResult]) -> Dict:
        """Generate comprehensive session report"""
        
        self.session_stats['session_end'] = datetime.now().isoformat()
        
        # Calculate success rates by method
        api_results = [r for r in results if r.method.startswith('API')]
        browser_results = [r for r in results if r.method.startswith('BROWSER')]
        
        report = {
            'session_stats': self.session_stats,
            'performance_metrics': {
                'total_bids': len(results),
                'successful_bids': sum(1 for r in results if r.success),
                'failed_bids': sum(1 for r in results if not r.success),
                'success_rate': (sum(1 for r in results if r.success) / len(results) * 100) if results else 0,
                'api_success_rate': (sum(1 for r in api_results if r.success) / len(api_results) * 100) if api_results else 0,
                'browser_success_rate': (sum(1 for r in browser_results if r.success) / len(browser_results) * 100) if browser_results else 0,
                'average_execution_time': sum(r.execution_time for r in results) / len(results) if results else 0,
                'total_amount_bid': sum(r.bid_amount for r in results if r.success)
            },
            'bid_results': [asdict(result) for result in results]
        }
        
        # Save report
        os.makedirs('data_outputs', exist_ok=True)
        report_path = f"data_outputs/real_bidding_session_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📊 SESSION REPORT:")
        self.logger.info(f"   Total Bids: {report['performance_metrics']['total_bids']}")
        self.logger.info(f"   Success Rate: {report['performance_metrics']['success_rate']:.1f}%")
        self.logger.info(f"   API Success: {report['performance_metrics']['api_success_rate']:.1f}%")
        self.logger.info(f"   Browser Success: {report['performance_metrics']['browser_success_rate']:.1f}%")
        self.logger.info(f"   Avg Execution: {report['performance_metrics']['average_execution_time']:.2f}s")
        self.logger.info(f"   Total Amount: ${report['performance_metrics']['total_amount_bid']:.2f}")
        self.logger.info(f"   Report: {report_path}")
        
        return report
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'conn'):
            self.conn.close()
        self.logger.info("🧹 Real bidding system cleanup complete")

async def main():
    """Test the real bidding system"""
    
    print("🎯 REAL BIDDING SYSTEM TEST")
    print("="*50)
    
    # Create test bid requests
    test_bids = [
        BidRequest(
            lot_id=35863830,
            auction_id=48796,
            bid_amount=1.00,
            max_bid=5.00,
            priority="HIGH",
            timing_strategy="IMMEDIATE",
            notes="Test bid #1 - ECOVACS Robot Vacuum"
        ),
        BidRequest(
            lot_id=35863830,
            auction_id=48796,
            bid_amount=2.00,
            max_bid=10.00,
            priority="MEDIUM",
            timing_strategy="LAST_MINUTE",
            notes="Test bid #2 - Higher amount"
        )
    ]
    
    # Initialize system (DRY RUN mode)
    bidding_system = RealBiddingSystem(dry_run=True)
    
    try:
        # Discover endpoints first
        print("\n🔍 Discovering bidding endpoints...")
        endpoints = await bidding_system.discover_bidding_endpoints()
        print(f"Found {len(endpoints)} potential endpoints")
        
        # Execute test bids
        print(f"\n🎯 Executing {len(test_bids)} test bids...")
        results = await bidding_system.execute_bidding_queue(test_bids)
        
        print(f"\n✅ Test completed!")
        for i, result in enumerate(results, 1):
            print(f"   Bid {i}: {'SUCCESS' if result.success else 'FAILED'} - {result.message}")
            
    finally:
        bidding_system.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 