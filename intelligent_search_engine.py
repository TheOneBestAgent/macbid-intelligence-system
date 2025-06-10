#!/usr/bin/env python3
"""
Mac.bid Intelligence System - Intelligent Search Engine
Phase 5: Advanced Search and Discovery Features

Provides intelligent search capabilities with saved searches, alerts,
and advanced filtering for Mac.bid auction data.
"""

import json
import sqlite3
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentSearchEngine:
    """Advanced search engine for Mac.bid auction data"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.db_path = self.base_dir / 'databases' / 'search_intelligence.db'
        self.credentials_path = Path.home() / '.macbid_scraper' / 'credentials.json'
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Load credentials
        self.credentials = self._load_credentials()
        
        # Search configuration
        self.typesense_config = {
            'url': 'https://xczkhpt94lod37gqp.a1.typesense.net/multi_search',
            'api_key': 'jxX8RU6YVOkm9esgd9buaYjulIWv6N52',
            'collection': 'prod_macdiscount_alias'
        }
    
    def _init_database(self):
        """Initialize search intelligence database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Saved searches table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS saved_searches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        search_criteria TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP,
                        use_count INTEGER DEFAULT 0,
                        notifications_enabled BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # Search alerts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        search_criteria TEXT NOT NULL,
                        notification_methods TEXT NOT NULL,
                        frequency_minutes INTEGER DEFAULT 15,
                        last_checked TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Search history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        search_query TEXT NOT NULL,
                        filters TEXT,
                        results_count INTEGER,
                        execution_time REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Search results cache
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        search_hash TEXT UNIQUE NOT NULL,
                        search_criteria TEXT NOT NULL,
                        results TEXT NOT NULL,
                        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL
                    )
                ''')
                
                conn.commit()
                logger.info("Search intelligence database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load Mac.bid credentials"""
        try:
            if self.credentials_path.exists():
                with open(self.credentials_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
        
        return {}
    
    def search_auctions(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Perform intelligent auction search"""
        start_time = time.time()
        
        try:
            # Build search query
            search_query = self._build_search_query(criteria)
            
            # Check cache first
            cached_results = self._get_cached_results(search_query)
            if cached_results:
                logger.info("Returning cached search results")
                return cached_results
            
            # Perform live search
            results = self._execute_search(search_query)
            
            # Apply intelligent filtering and ranking
            enhanced_results = self._enhance_results(results, criteria)
            
            # Cache results
            self._cache_results(search_query, enhanced_results)
            
            # Log search
            execution_time = time.time() - start_time
            self._log_search(criteria, len(enhanced_results.get('items', [])), execution_time)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return {'items': [], 'total': 0, 'error': str(e)}
    
    def _build_search_query(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Build Typesense search query from criteria"""
        query = {
            'searches': [{
                'collection': 'prod_macdiscount_alias',
                'q': criteria.get('keywords', '*'),
                'query_by': 'product_name,embedding,description,keywords,upc,inventory_id,auction_title',
                'exclude_fields': 'description,keywords,bid_delta,embedding',
                'vector_query': 'embedding:([], distance_threshold:0.18)',
                'drop_tokens_threshold': 0,
                'num_typos': '1,0,0,0,0,0,0',
                'use_cache': True,
                'sort_by': 'ranking_weight:desc',
                'highlight_full_fields': 'product_name,embedding,description,keywords,upc,inventory_id,auction_title',
                'facet_by': 'auction_location,category,condition,current_bid,expected_close_date,is_open,is_transferrable,retail_price',
                'max_facet_values': 20,
                'per_page': 96,
                'page': 1
            }]
        }
        
        # Add filters
        filters = []
        
        # Always filter for open auctions
        filters.append("is_open:=[1]")
        
        # Location filter
        if criteria.get('location'):
            filters.append(f"auction_location:=[`{criteria['location']}`]")
        else:
            # Default to South Carolina locations
            sc_locations = ['Anderson', 'Gastonia', 'Greenville', 'Rock Hill', 'Spartanburg']
            location_filter = ','.join([f'`{loc}`' for loc in sc_locations])
            filters.append(f"auction_location:=[{location_filter}]")
        
        # Category filter
        if criteria.get('category'):
            filters.append(f"category:=[`{criteria['category']}`]")
        
        # Price range filter
        if criteria.get('min_price'):
            filters.append(f"current_bid:>={criteria['min_price']}")
        if criteria.get('max_price'):
            filters.append(f"current_bid:<={criteria['max_price']}")
        
        # Condition filter
        if criteria.get('condition'):
            filters.append(f"condition:=[`{criteria['condition']}`]")
        
        # Status filter
        if criteria.get('status'):
            if criteria['status'] == 'ending-soon':
                # Items ending in next 2 hours
                end_time = int((datetime.now() + timedelta(hours=2)).timestamp())
                filters.append(f"expected_close_date:<{end_time}")
            elif criteria['status'] == 'new':
                # Items added in last 24 hours
                start_time = int((datetime.now() - timedelta(hours=24)).timestamp())
                filters.append(f"created_at:>{start_time}")
            elif criteria['status'] == 'no-bids':
                filters.append("current_bid:=0")
        
        if filters:
            query['searches'][0]['filter_by'] = ' && '.join(filters)
        
        return query
    
    def _execute_search(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search against Typesense API"""
        try:
            headers = {
                'X-TYPESENSE-API-KEY': self.typesense_config['api_key'],
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.typesense_config['url'],
                headers=headers,
                json=query,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    return data['results'][0]
            
            logger.warning(f"Search API returned status {response.status_code}")
            return {'hits': [], 'found': 0}
            
        except Exception as e:
            logger.error(f"Error executing search: {e}")
            return {'hits': [], 'found': 0}
    
    def _enhance_results(self, results: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance search results with intelligence and scoring"""
        items = []
        
        for hit in results.get('hits', []):
            item_data = hit.get('document', {})
            
            # Calculate opportunity score
            opportunity_score = self._calculate_opportunity_score(item_data)
            
            # Add enhanced data
            enhanced_item = {
                'lot_id': item_data.get('id'),
                'product_name': item_data.get('product_name', ''),
                'title': item_data.get('product_name', ''),
                'description': item_data.get('description', ''),
                'category': item_data.get('category', ''),
                'auction_location': item_data.get('auction_location', ''),
                'current_bid': item_data.get('current_bid', 0),
                'retail_price': item_data.get('retail_price'),
                'instant_win_price': item_data.get('instant_win_price'),
                'expected_close_date': item_data.get('expected_close_date'),
                'condition': item_data.get('condition', ''),
                'images': item_data.get('images', []),
                'is_open': item_data.get('is_open', 1),
                'is_transferrable': item_data.get('is_transferrable', 0),
                'opportunity_score': opportunity_score,
                'relevance_score': hit.get('text_match', 0),
                'time_left': self._calculate_time_left(item_data.get('expected_close_date')),
                'price_trend': self._analyze_price_trend(item_data),
                'competition_level': self._assess_competition(item_data)
            }
            
            items.append(enhanced_item)
        
        # Sort by relevance and opportunity
        items.sort(key=lambda x: (x['opportunity_score'], x['relevance_score']), reverse=True)
        
        return {
            'items': items,
            'total': results.get('found', 0),
            'search_time': results.get('search_time_ms', 0),
            'enhanced': True
        }
    
    def _calculate_opportunity_score(self, item: Dict[str, Any]) -> int:
        """Calculate opportunity score for an item"""
        score = 50  # Base score
        
        try:
            current_bid = float(item.get('current_bid', 0))
            retail_price = float(item.get('retail_price', 0))
            instant_win_price = float(item.get('instant_win_price', 0))
            
            # Price opportunity (lower current bid vs retail/instant win = higher score)
            reference_price = retail_price if retail_price > 0 else instant_win_price
            if reference_price > 0 and current_bid > 0:
                price_ratio = current_bid / reference_price
                if price_ratio < 0.3:
                    score += 30
                elif price_ratio < 0.5:
                    score += 20
                elif price_ratio < 0.7:
                    score += 10
            elif current_bid == 0:
                score += 25  # No bids yet
            
            # Transferrable items get bonus
            if item.get('is_transferrable', 0):
                score += 10
            
            # Time remaining factor
            end_time = item.get('expected_close_date')
            if end_time:
                time_left = self._calculate_time_left(end_time)
                if 'h' in time_left and int(time_left.split('h')[0]) < 2:
                    score += 15  # Ending soon bonus
                elif 'd' in time_left:
                    score += 5   # Time to research
            
            # Category bonuses
            category = item.get('category', '').lower()
            if 'electronics' in category:
                score += 10
            elif 'tools' in category:
                score += 8
            
            # Ensure score is within bounds
            score = max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
        
        return score
    
    def _calculate_time_left(self, end_time: Any) -> str:
        """Calculate time remaining for auction"""
        try:
            if isinstance(end_time, (int, float)):
                end_dt = datetime.fromtimestamp(end_time)
            else:
                end_dt = datetime.fromisoformat(str(end_time))
            
            now = datetime.now()
            if end_dt <= now:
                return "Ended"
            
            diff = end_dt - now
            days = diff.days
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60
            
            if days > 0:
                return f"{days}d {hours}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except Exception:
            return "Unknown"
    
    def _analyze_price_trend(self, item: Dict[str, Any]) -> str:
        """Analyze price trend for item"""
        # This would integrate with historical price data
        # For now, return basic analysis
        bid_count = item.get('bid_count', 0)
        
        if bid_count == 0:
            return "stable"
        elif bid_count < 3:
            return "slow"
        elif bid_count > 8:
            return "rising"
        else:
            return "moderate"
    
    def _assess_competition(self, item: Dict[str, Any]) -> str:
        """Assess competition level for item"""
        bid_count = item.get('bid_count', 0)
        
        if bid_count == 0:
            return "none"
        elif bid_count < 3:
            return "low"
        elif bid_count < 8:
            return "moderate"
        else:
            return "high"
    
    def save_search(self, name: str, description: str, criteria: Dict[str, Any], 
                   notifications: bool = False) -> Dict[str, Any]:
        """Save a search for future use"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO saved_searches 
                    (name, description, search_criteria, notifications_enabled)
                    VALUES (?, ?, ?, ?)
                ''', (name, description, json.dumps(criteria), notifications))
                
                search_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Saved search '{name}' with ID {search_id}")
                return {'success': True, 'id': search_id}
                
        except Exception as e:
            logger.error(f"Error saving search: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_saved_searches(self) -> List[Dict[str, Any]]:
        """Get all saved searches"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, name, description, search_criteria, 
                           created_at, last_used, use_count, notifications_enabled
                    FROM saved_searches
                    ORDER BY last_used DESC, created_at DESC
                ''')
                
                searches = []
                for row in cursor.fetchall():
                    searches.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'criteria': json.loads(row[3]),
                        'created_at': row[4],
                        'last_used': row[5],
                        'use_count': row[6],
                        'notifications_enabled': bool(row[7])
                    })
                
                return searches
                
        except Exception as e:
            logger.error(f"Error getting saved searches: {e}")
            return []
    
    def create_alert(self, name: str, criteria: Dict[str, Any], 
                    notification_methods: List[str], frequency: int = 15) -> Dict[str, Any]:
        """Create a search alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO search_alerts 
                    (name, search_criteria, notification_methods, frequency_minutes)
                    VALUES (?, ?, ?, ?)
                ''', (name, json.dumps(criteria), json.dumps(notification_methods), frequency))
                
                alert_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created search alert '{name}' with ID {alert_id}")
                return {'success': True, 'id': alert_id}
                
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active search alerts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, name, search_criteria, notification_methods,
                           frequency_minutes, last_checked, active, created_at
                    FROM search_alerts
                    WHERE active = TRUE
                    ORDER BY created_at DESC
                ''')
                
                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        'id': row[0],
                        'name': row[1],
                        'criteria': json.loads(row[2]),
                        'notification_methods': json.loads(row[3]),
                        'frequency_minutes': row[4],
                        'last_checked': row[5],
                        'active': bool(row[6]),
                        'created_at': row[7]
                    })
                
                return alerts
                
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def _get_cached_results(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached search results if available and not expired"""
        try:
            search_hash = str(hash(json.dumps(query, sort_keys=True)))
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT results FROM search_cache 
                    WHERE search_hash = ? AND expires_at > datetime('now')
                ''', (search_hash,))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                    
        except Exception as e:
            logger.error(f"Error getting cached results: {e}")
        
        return None
    
    def _cache_results(self, query: Dict[str, Any], results: Dict[str, Any]):
        """Cache search results"""
        try:
            search_hash = str(hash(json.dumps(query, sort_keys=True)))
            expires_at = datetime.now() + timedelta(minutes=15)  # Cache for 15 minutes
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO search_cache 
                    (search_hash, search_criteria, results, expires_at)
                    VALUES (?, ?, ?, ?)
                ''', (search_hash, json.dumps(query), json.dumps(results), expires_at))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error caching results: {e}")
    
    def _log_search(self, criteria: Dict[str, Any], results_count: int, execution_time: float):
        """Log search for analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO search_history 
                    (search_query, filters, results_count, execution_time)
                    VALUES (?, ?, ?, ?)
                ''', (
                    criteria.get('keywords', ''),
                    json.dumps(criteria),
                    results_count,
                    execution_time
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging search: {e}")

def main():
    """Test the intelligent search engine"""
    search_engine = IntelligentSearchEngine()
    
    # Test search
    criteria = {
        'keywords': 'MacBook',
        'category': 'electronics',
        'location': 'Spartanburg',
        'max_price': 1000
    }
    
    print("🔍 Testing Intelligent Search Engine...")
    results = search_engine.search_auctions(criteria)
    
    print(f"📊 Found {results['total']} items")
    for item in results['items'][:3]:
        print(f"  • {item['title']} - ${item['current_bid']} (Score: {item['opportunity_score']})")
    
    # Test save search
    save_result = search_engine.save_search(
        "MacBook Deals",
        "Looking for MacBook deals under $1000",
        criteria,
        notifications=True
    )
    print(f"💾 Save search result: {save_result}")

if __name__ == '__main__':
    main() 