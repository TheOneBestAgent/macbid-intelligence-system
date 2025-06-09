#!/usr/bin/env python3
"""
Typesense Data Fixer
Analyzes why Typesense is returning 0 lots and fixes search parameters
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Import discovered authentication
from macbid_auth_config import MACBID_HEADERS, MACBID_CUSTOMER_ID, MACBID_BASE_URL, FIREBASE_SESSION_ID, SESSION_ID

class TypesenseDataFixer:
    def __init__(self):
        self.base_url = MACBID_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(MACBID_HEADERS)
        
        # REAL working Typesense configuration from existing code
        self.typesense_url = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
        self.typesense_api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def analyze_typesense_collection(self) -> Dict:
        """Analyze the Typesense collection to understand its structure"""
        print("🔍 ANALYZING TYPESENSE COLLECTION STRUCTURE")
        print("=" * 50)
        
        try:
            # Try to get collection info
            collection_url = "https://xczkhpt94lod37gqp.a1.typesense.net/collections/lots"
            headers = {'X-TYPESENSE-API-KEY': self.typesense_api_key}
            
            response = self.session.get(f"{collection_url}?x-typesense-api-key={self.typesense_api_key}", headers=headers)
            
            if response.status_code == 200:
                collection_info = response.json()
                print("✅ Collection Info Retrieved:")
                print(f"   Name: {collection_info.get('name', 'Unknown')}")
                print(f"   Documents: {collection_info.get('num_documents', 0)}")
                print(f"   Fields: {len(collection_info.get('fields', []))}")
                
                # Show field structure
                fields = collection_info.get('fields', [])
                print("\n📋 Collection Fields:")
                for field in fields[:10]:  # Show first 10 fields
                    print(f"   • {field.get('name', 'Unknown')} ({field.get('type', 'Unknown')})")
                
                return collection_info
            else:
                print(f"❌ Collection info failed: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error analyzing collection: {e}")
            return {}
    
    def test_different_search_strategies(self) -> Dict:
        """Test different search strategies to find data"""
        print("\n🧪 TESTING DIFFERENT SEARCH STRATEGIES")
        print("=" * 45)
        
        strategies = {
            'broad_search': False,
            'no_filters': False,
            'different_collections': False,
            'date_ranges': False,
            'location_variations': False
        }
        
        headers = {
            'X-TYPESENSE-API-KEY': self.typesense_api_key,
            'Content-Type': 'application/json'
        }
        
        # Strategy 1: Broad search with no filters
        try:
            print("\n🔍 Strategy 1: Broad search (no filters)...")
            payload = {
                "searches": [
                    {
                        "collection": "lots",
                        "q": "*",
                        "query_by": "product_name,description,keywords",
                        "per_page": 10,
                        "page": 1
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.typesense_url}?x-typesense-api-key={self.typesense_api_key}",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    found = data['results'][0].get('found', 0)
                    print(f"   ✅ Broad search: {found} lots found")
                    strategies['broad_search'] = found > 0
                else:
                    print("   ❌ Broad search: No results structure")
            else:
                print(f"   ❌ Broad search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Broad search error: {e}")
        
        # Strategy 2: Try different query fields
        try:
            print("\n🔍 Strategy 2: Different query fields...")
            query_field_sets = [
                "product_name",
                "description", 
                "keywords",
                "upc",
                "inventory_id",
                "*"  # All fields
            ]
            
            for query_by in query_field_sets:
                payload = {
                    "searches": [
                        {
                            "collection": "lots",
                            "q": "*",
                            "query_by": query_by,
                            "per_page": 5,
                            "page": 1
                        }
                    ]
                }
                
                response = self.session.post(
                    f"{self.typesense_url}?x-typesense-api-key={self.typesense_api_key}",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and len(data['results']) > 0:
                        found = data['results'][0].get('found', 0)
                        if found > 0:
                            print(f"   ✅ Query field '{query_by}': {found} lots")
                            strategies['no_filters'] = True
                            break
                        else:
                            print(f"   ❌ Query field '{query_by}': 0 lots")
                            
        except Exception as e:
            print(f"   ❌ Query fields test error: {e}")
        
        # Strategy 3: Try different date ranges
        try:
            print("\n🔍 Strategy 3: Different date ranges...")
            
            # Try searching for lots from different time periods
            date_filters = [
                "",  # No date filter
                "created_at:>2024-01-01",
                "updated_at:>2024-01-01", 
                "auction_end_date:>2024-01-01",
                "is_active:=true",
                "status:=active"
            ]
            
            for date_filter in date_filters:
                payload = {
                    "searches": [
                        {
                            "collection": "lots",
                            "q": "*",
                            "query_by": "product_name,description",
                            "filter_by": date_filter if date_filter else None,
                            "per_page": 5,
                            "page": 1
                        }
                    ]
                }
                
                # Remove None filter_by
                if not date_filter:
                    del payload["searches"][0]["filter_by"]
                
                response = self.session.post(
                    f"{self.typesense_url}?x-typesense-api-key={self.typesense_api_key}",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and len(data['results']) > 0:
                        found = data['results'][0].get('found', 0)
                        if found > 0:
                            print(f"   ✅ Date filter '{date_filter or 'none'}': {found} lots")
                            strategies['date_ranges'] = True
                            break
                        else:
                            print(f"   ❌ Date filter '{date_filter or 'none'}': 0 lots")
                            
        except Exception as e:
            print(f"   ❌ Date ranges test error: {e}")
        
        # Strategy 4: Try location variations
        try:
            print("\n🔍 Strategy 4: Location variations...")
            
            location_filters = [
                "",  # No location filter
                "location:=Rock Hill",
                "location:=Anderson", 
                "auction_location:=Rock Hill",
                "auction_location:=Anderson",
                "warehouse:=SC",
                "state:=SC"
            ]
            
            for location_filter in location_filters:
                payload = {
                    "searches": [
                        {
                            "collection": "lots",
                            "q": "*",
                            "query_by": "product_name,description",
                            "filter_by": location_filter if location_filter else None,
                            "per_page": 5,
                            "page": 1
                        }
                    ]
                }
                
                # Remove None filter_by
                if not location_filter:
                    del payload["searches"][0]["filter_by"]
                
                response = self.session.post(
                    f"{self.typesense_url}?x-typesense-api-key={self.typesense_api_key}",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and len(data['results']) > 0:
                        found = data['results'][0].get('found', 0)
                        if found > 0:
                            print(f"   ✅ Location filter '{location_filter or 'none'}': {found} lots")
                            strategies['location_variations'] = True
                            break
                        else:
                            print(f"   ❌ Location filter '{location_filter or 'none'}': 0 lots")
                            
        except Exception as e:
            print(f"   ❌ Location variations test error: {e}")
        
        return strategies
    
    def find_working_search_parameters(self) -> Dict:
        """Find working search parameters that return data"""
        print("\n🎯 FINDING WORKING SEARCH PARAMETERS")
        print("=" * 40)
        
        headers = {
            'X-TYPESENSE-API-KEY': self.typesense_api_key,
            'Content-Type': 'application/json'
        }
        
        # Test the most basic possible search
        try:
            payload = {
                "searches": [
                    {
                        "collection": "lots",
                        "q": "",  # Empty query
                        "per_page": 10,
                        "page": 1
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.typesense_url}?x-typesense-api-key={self.typesense_api_key}",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Basic search response received")
                print(f"   Response structure: {list(data.keys())}")
                
                if 'results' in data:
                    print(f"   Results array length: {len(data['results'])}")
                    if len(data['results']) > 0:
                        result = data['results'][0]
                        print(f"   First result keys: {list(result.keys())}")
                        found = result.get('found', 0)
                        print(f"   Documents found: {found}")
                        
                        if found > 0:
                            hits = result.get('hits', [])
                            if hits:
                                first_hit = hits[0]
                                doc = first_hit.get('document', {})
                                print(f"   Sample document fields: {list(doc.keys())[:10]}")
                                
                                return {
                                    'working': True,
                                    'found': found,
                                    'sample_fields': list(doc.keys()),
                                    'working_payload': payload
                                }
                
                return {
                    'working': False,
                    'found': 0,
                    'response_structure': data,
                    'issue': 'No documents found in collection'
                }
            else:
                return {
                    'working': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text[:200]
                }
                
        except Exception as e:
            return {
                'working': False,
                'error': str(e)
            }
    
    def fix_typesense_search(self) -> Dict:
        """Attempt to fix Typesense search and find working parameters"""
        print("\n🔧 ATTEMPTING TYPESENSE SEARCH FIX")
        print("=" * 40)
        
        # Step 1: Analyze collection
        collection_info = self.analyze_typesense_collection()
        
        # Step 2: Test different strategies
        strategies = self.test_different_search_strategies()
        
        # Step 3: Find working parameters
        working_params = self.find_working_search_parameters()
        
        # Step 4: Generate recommendations
        recommendations = []
        
        if working_params.get('working'):
            recommendations.append("✅ Basic Typesense search is working")
            recommendations.append(f"✅ Found {working_params['found']} documents")
        else:
            recommendations.append("❌ Typesense collection appears to be empty")
            recommendations.append("⚠️  May need to refresh/repopulate the collection")
        
        if collection_info.get('num_documents', 0) == 0:
            recommendations.append("❌ Collection has 0 documents - needs data refresh")
        
        if any(strategies.values()):
            working_strategies = [k for k, v in strategies.items() if v]
            recommendations.append(f"✅ Working strategies: {', '.join(working_strategies)}")
        
        return {
            'collection_info': collection_info,
            'strategies_tested': strategies,
            'working_parameters': working_params,
            'recommendations': recommendations,
            'fixed': working_params.get('working', False)
        }

def main():
    """Main execution function"""
    fixer = TypesenseDataFixer()
    
    print("🔍 TYPESENSE DATA FIXER")
    print("=" * 30)
    
    # Run comprehensive fix
    results = fixer.fix_typesense_search()
    
    print(f"\n📊 TYPESENSE FIX RESULTS:")
    print("=" * 30)
    
    if results['fixed']:
        print("🎉 Typesense search is WORKING!")
        working_params = results['working_parameters']
        print(f"   Documents found: {working_params['found']}")
        print(f"   Sample fields: {working_params.get('sample_fields', [])[:5]}")
    else:
        print("❌ Typesense search still has issues")
        
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in results['recommendations']:
        print(f"   {rec}")

if __name__ == "__main__":
    main() 