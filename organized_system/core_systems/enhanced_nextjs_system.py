#!/usr/bin/env python3
"""
Enhanced NextJS Integration System
Using exact parameters from macbid_breakdown analysis
"""

import requests
import json
import time
from datetime import datetime
import logging

class EnhancedNextJSSystem:
    def __init__(self):
        self.session = requests.Session()
        
        # EXACT BUILD ID from macbid_breakdown
        self.nextjs_build_id = "AslxUFb4wF5GgYRFXlpoC"
        
        # EXACT HEADERS from macbid_breakdown
        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.6",
            "priority": "u=1, i",
            "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "x-nextjs-data": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        })
        
        # EXACT TYPESENSE CONFIG from macbid_breakdown
        self.typesense_url = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
        self.typesense_api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
        
        # USER DATA from macbid_breakdown
        self.user_id = "2710619"
        self.braze_api_key = "ce8b7722-883a-498b-90ff-0aef9d0f0e62"
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Authenticate session
        self._authenticate_session()
    
    def _authenticate_session(self):
        """Authenticate session using exact macbid_breakdown patterns"""
        try:
            # Set referrer policy exactly like macbid_breakdown
            self.session.headers.update({
                "referrer": "https://www.mac.bid/",
                "referrerPolicy": "strict-origin-when-cross-origin"
            })
            
            # Test authentication with location endpoint
            test_url = f"https://www.mac.bid/_next/data/{self.nextjs_build_id}/locations/rock-hill.json?loc=rock-hill"
            response = self.session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("✅ NextJS authentication successful")
                return True
            else:
                self.logger.warning(f"⚠️ NextJS auth returned {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ NextJS authentication failed: {e}")
            return False
    
    def get_location_data(self, location):
        """Get location-specific data using exact macbid_breakdown endpoint"""
        try:
            url = f"https://www.mac.bid/_next/data/{self.nextjs_build_id}/locations/{location}.json?loc={location}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Location data retrieved for {location}")
                return data
            else:
                self.logger.warning(f"⚠️ Location data failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Location data error: {e}")
            return None
    
    def enhanced_typesense_search(self, location="Rock Hill", page=1, per_page=96):
        """Enhanced Typesense search using exact macbid_breakdown parameters"""
        try:
            # EXACT REQUEST BODY from macbid_breakdown
            search_body = {
                "searches": [
                    {
                        "query_by": "product_name,embedding,description,keywords,upc,inventory_id,auction_title",
                        "exclude_fields": "description,keywords,bid_delta,embedding",
                        "vector_query": "embedding:([], distance_threshold:0.18)",
                        "drop_tokens_threshold": 0,
                        "num_typos": "1,0,0,0,0,0,0",
                        "use_cache": True,
                        "sort_by": "ranking_weight:desc",
                        "highlight_full_fields": "product_name,embedding,description,keywords,upc,inventory_id,auction_title",
                        "collection": "prod_macdiscount_alias",
                        "q": "*",
                        "facet_by": "auction_location,category,condition,current_bid,expected_close_date,is_open,is_transferrable,retail_price",
                        "filter_by": f"auction_location:=[`{location}`] && is_open:=[1]",
                        "max_facet_values": 20,
                        "page": page,
                        "per_page": per_page
                    }
                ]
            }
            
            # EXACT HEADERS from macbid_breakdown
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.6",
                "content-type": "text/plain",
                "priority": "u=1, i",
                "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
                "sec-gpc": "1",
                "referrer": "https://www.mac.bid/",
                "referrerPolicy": "strict-origin-when-cross-origin"
            }
            
            url = f"{self.typesense_url}?x-typesense-api-key={self.typesense_api_key}"
            
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(search_body),
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Enhanced Typesense search successful for {location}")
                return data
            else:
                self.logger.warning(f"⚠️ Enhanced Typesense search failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Enhanced Typesense search error: {e}")
            return None
    
    def get_lot_data(self, lot_id):
        """Get specific lot data using NextJS endpoint"""
        try:
            # Try multiple endpoint patterns
            endpoints = [
                f"https://www.mac.bid/_next/data/{self.nextjs_build_id}/lot/mac_lot_{lot_id}.json",
                f"https://www.mac.bid/_next/data/{self.nextjs_build_id}/lot/{lot_id}.json",
                f"https://www.mac.bid/_next/data/{self.nextjs_build_id}/lots/{lot_id}.json"
            ]
            
            for url in endpoints:
                try:
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.logger.info(f"✅ Lot data retrieved for {lot_id}")
                        return data
                        
                except Exception as e:
                    continue
            
            self.logger.warning(f"⚠️ No lot data found for {lot_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Lot data error: {e}")
            return None
    
    def sync_braze_data(self):
        """Sync with Braze analytics using exact macbid_breakdown parameters"""
        try:
            url = "https://sdk.iad-07.braze.com/api/v3/content_cards/sync"
            
            headers = {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.6",
                "braze-sync-retry-count": "0",
                "content-type": "application/json",
                "priority": "u=1, i",
                "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
                "sec-gpc": "1",
                "x-braze-api-key": self.braze_api_key,
                "x-braze-contentcardsrequest": "true",
                "x-braze-datarequest": "true",
                "x-braze-last-req-ms-ago": "17647",
                "x-braze-req-attempt": "1",
                "x-braze-req-tokens-remaining": "25",
                "x-requested-with": "XMLHttpRequest",
                "referrer": "https://www.mac.bid/",
                "referrerPolicy": "strict-origin-when-cross-origin"
            }
            
            body = {
                "api_key": self.braze_api_key,
                "time": int(time.time()),
                "sdk_version": "5.7.0",
                "device_id": "6557c69b-3239-8d82-7b30-ec5862a4de57",
                "user_id": self.user_id,
                "last_full_sync_at": int(time.time()) - 18,
                "last_card_updated_at": 0
            }
            
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(body),
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("✅ Braze sync successful")
                return True
            else:
                self.logger.warning(f"⚠️ Braze sync failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Braze sync error: {e}")
            return False
    
    def comprehensive_discovery(self, exclude_today=True):
        """Comprehensive discovery using all enhanced methods"""
        results = {
            'locations': {},
            'lots': [],
            'total_found': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        locations = ["Anderson", "Gastonia", "Greenville", "Rock Hill", "Spartanburg"]
        
        self.logger.info("🚀 Starting comprehensive enhanced discovery...")
        
        # Sync with Braze first
        self.sync_braze_data()
        
        for location in locations:
            self.logger.info(f"📍 Processing {location}...")
            
            # Get location data
            location_data = self.get_location_data(location.lower().replace(" ", "-"))
            if location_data:
                results['locations'][location] = location_data
            
            # Get lots for this location
            typesense_data = self.enhanced_typesense_search(location)
            if typesense_data and 'results' in typesense_data:
                for result in typesense_data['results']:
                    if 'hits' in result:
                        for hit in result['hits']:
                            lot = hit.get('document', {})
                            
                            # Filter out lots closing today if requested
                            if exclude_today:
                                close_date = lot.get('expected_close_date', '')
                                if '2025-06-07' in str(close_date):
                                    continue
                            
                            results['lots'].append(lot)
                            results['total_found'] += 1
        
        self.logger.info(f"✅ Enhanced discovery complete: {results['total_found']} lots found")
        return results

if __name__ == "__main__":
    # Test the enhanced system
    system = EnhancedNextJSSystem()
    
    print("🧪 TESTING ENHANCED NEXTJS SYSTEM")
    print("=" * 50)
    
    # Test location data
    print("\n📍 Testing location data...")
    rock_hill_data = system.get_location_data("rock-hill")
    if rock_hill_data:
        print("✅ Location data working!")
    
    # Test enhanced Typesense
    print("\n🔍 Testing enhanced Typesense...")
    search_results = system.enhanced_typesense_search("Rock Hill", per_page=5)
    if search_results:
        print("✅ Enhanced Typesense working!")
    
    # Test comprehensive discovery
    print("\n🚀 Testing comprehensive discovery...")
    discovery_results = system.comprehensive_discovery()
    print(f"✅ Found {discovery_results['total_found']} lots total!")
    
    print("\n🎉 ENHANCED NEXTJS SYSTEM READY!") 