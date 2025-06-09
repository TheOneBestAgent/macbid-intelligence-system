#!/usr/bin/env python3
"""
🚀 Parallel Multi-Source Discovery System
Combines Typesense, NextJS, and API sources simultaneously for MAXIMUM SPEED
🔐 REQUIRES AUTHENTICATION BEFORE ANY OPERATIONS
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Set, Tuple
from concurrent.futures import ThreadPoolExecutor
import sys

# Import authentication manager (REQUIRED FIRST)
sys.path.append('.')
from core_systems.authentication_manager import require_authentication, get_authenticated_headers, get_customer_id

# Import all our discovery systems
from discovery_systems.typesense_all_lots_scanner import TypesenseAllLotsScanner
from core_systems.nextjs_integration_system import NextJSIntegrationSystem
from discovery_systems.comprehensive_warehouse_scanner import ComprehensiveWarehouseScanner

class ParallelDiscoverySystem:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Authentication will be set up in run_parallel_discovery
        self.auth_manager = None
        self.authenticated_headers = None
        
        # Initialize all discovery systems (will be configured with auth later)
        self.typesense_scanner = None
        self.nextjs_system = None
        self.warehouse_scanner = None
        
        # Combined results
        self.all_discovered_lots: Dict[str, Dict] = {}
        self.discovery_stats = {
            'start_time': None,
            'end_time': None,
            'total_duration': 0,
            'typesense_lots': 0,
            'nextjs_lots': 0,
            'warehouse_lots': 0,
            'unique_lots_total': 0,
            'data_sources_used': 0
        }
        
        # Performance tracking
        self.source_performance = {
            'typesense': {'start': None, 'end': None, 'lots': 0, 'status': 'pending'},
            'nextjs': {'start': None, 'end': None, 'lots': 0, 'status': 'pending'},
            'warehouse': {'start': None, 'end': None, 'lots': 0, 'status': 'pending'}
        }
    
    async def run_typesense_discovery(self) -> Tuple[str, List[Dict]]:
        """Run Typesense discovery in parallel"""
        source_name = "typesense"
        self.source_performance[source_name]['start'] = time.time()
        self.source_performance[source_name]['status'] = 'running'
        
        try:
            self.logger.info("🔍 Starting Typesense discovery...")
            
            # Run Typesense scanner
            await self.typesense_scanner.run_typesense_discovery()
            lots = list(self.typesense_scanner.discovered_lots.values())
            
            self.source_performance[source_name]['lots'] = len(lots)
            self.source_performance[source_name]['status'] = 'completed'
            self.logger.info(f"✅ Typesense completed: {len(lots):,} lots")
            
            return source_name, lots
            
        except Exception as e:
            self.source_performance[source_name]['status'] = 'failed'
            self.logger.error(f"❌ Typesense discovery failed: {e}")
            return source_name, []
        finally:
            self.source_performance[source_name]['end'] = time.time()
    
    async def run_nextjs_discovery(self) -> Tuple[str, List[Dict]]:
        """Run NextJS discovery in parallel - combines Typesense discovery with NextJS bid extraction"""
        source_name = "nextjs"
        self.source_performance[source_name]['start'] = time.time()
        self.source_performance[source_name]['status'] = 'running'
        
        try:
            self.logger.info("🔄 Starting NextJS discovery (Typesense + NextJS bid extraction)...")
            
            # Step 1: Use NextJS system to discover lots via Typesense
            discovered_lots = self.nextjs_system.discover_lots_typesense(max_pages=5)
            self.logger.info(f"📊 Discovered {len(discovered_lots)} lots via Typesense")
            
            # Step 2: Enhance with NextJS real-time bid data
            lots = []
            enhanced_count = 0
            
            # Limit to top 5 lots for testing NextJS integration (avoid lots closing today)
            test_lots = discovered_lots[:5] if discovered_lots else []
            self.logger.info(f"🧪 Testing NextJS enhancement on {len(test_lots)} lots (excluding today's closures)")
            
            for i, lot in enumerate(test_lots):
                auction_id = lot.get('auction_id')
                lot_id = lot.get('lot_id')
                
                if auction_id and lot_id:
                    try:
                        # Get real-time bid data from NextJS API
                        enhanced_data = self.nextjs_system.fetch_nextjs_lot_data(auction_id, lot_id)
                        if enhanced_data:
                            # Merge discovery and detailed data
                            combined_lot = {**lot, **enhanced_data}
                            combined_lot['data_source'] = 'nextjs_enhanced'
                            combined_lot['has_realtime_data'] = True
                            enhanced_count += 1
                        else:
                            # Use Typesense data as fallback
                            combined_lot = lot.copy()
                            combined_lot['data_source'] = 'typesense_fallback'
                            combined_lot['has_realtime_data'] = False
                        
                        lots.append(combined_lot)
                        
                        # Progress indicator for each lot
                        self.logger.info(f"   ✅ Enhanced lot {i + 1}/{len(test_lots)}: {lot.get('product_name', 'Unknown')[:30]}...")
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to enhance lot {lot_id}: {e}")
                        # Add original lot as fallback
                        lot['data_source'] = 'typesense_fallback'
                        lot['has_realtime_data'] = False
                        lots.append(lot)
                else:
                    # Add lot without enhancement
                    lot['data_source'] = 'typesense_only'
                    lot['has_realtime_data'] = False
                    lots.append(lot)
            
            # Add remaining lots that weren't tested for NextJS enhancement
            remaining_lots = discovered_lots[len(test_lots):]
            for lot in remaining_lots:
                lot['data_source'] = 'typesense_only'
                lot['has_realtime_data'] = False
                lots.append(lot)
            
            if remaining_lots:
                self.logger.info(f"📦 Added {len(remaining_lots)} remaining lots without NextJS enhancement")
            
            self.source_performance[source_name]['lots'] = len(lots)
            self.source_performance[source_name]['status'] = 'completed'
            self.logger.info(f"✅ NextJS completed: {len(lots):,} lots ({enhanced_count} with real-time data)")
            
            return source_name, lots
            
        except Exception as e:
            self.source_performance[source_name]['status'] = 'failed'
            self.logger.error(f"❌ NextJS discovery failed: {e}")
            return source_name, []
        finally:
            self.source_performance[source_name]['end'] = time.time()
    
    async def run_warehouse_discovery(self) -> Tuple[str, List[Dict]]:
        """Run warehouse API discovery in parallel"""
        source_name = "warehouse"
        self.source_performance[source_name]['start'] = time.time()
        self.source_performance[source_name]['status'] = 'running'
        
        try:
            self.logger.info("🏭 Starting warehouse API discovery...")
            
            # Run warehouse scanner
            lots = await self.warehouse_scanner.discover_all_lots()
            
            self.source_performance[source_name]['lots'] = len(lots)
            self.source_performance[source_name]['status'] = 'completed'
            self.logger.info(f"✅ Warehouse API completed: {len(lots):,} lots")
            
            return source_name, lots
            
        except Exception as e:
            self.source_performance[source_name]['status'] = 'failed'
            self.logger.error(f"❌ Warehouse discovery failed: {e}")
            return source_name, []
        finally:
            self.source_performance[source_name]['end'] = time.time()
    
    def merge_lot_data(self, lot_sources: List[Tuple[str, List[Dict]]]) -> Dict[str, Dict]:
        """Intelligently merge lot data from multiple sources"""
        merged_lots = {}
        
        for source_name, lots in lot_sources:
            self.logger.info(f"📊 Processing {len(lots):,} lots from {source_name}")
            
            for lot in lots:
                # Get unique lot identifier
                lot_id = (lot.get('lot_id') or lot.get('id') or 
                         lot.get('inventory_id') or lot.get('mac_lot_id') or '')
                
                if not lot_id:
                    continue
                
                # Convert to string for consistent keys
                lot_id = str(lot_id)
                
                if lot_id in merged_lots:
                    # Merge data from multiple sources
                    existing_lot = merged_lots[lot_id]
                    
                    # Prioritize data quality: NextJS > Typesense > Warehouse
                    if source_name == "nextjs":
                        # NextJS has the most detailed real-time data
                        merged_lots[lot_id] = {**existing_lot, **lot}
                        merged_lots[lot_id]['data_sources'] = existing_lot.get('data_sources', []) + [source_name]
                    elif source_name == "typesense" and "nextjs" not in existing_lot.get('data_sources', []):
                        # Typesense has comprehensive search data
                        merged_lots[lot_id] = {**existing_lot, **lot}
                        merged_lots[lot_id]['data_sources'] = existing_lot.get('data_sources', []) + [source_name]
                    else:
                        # Warehouse API provides additional coverage
                        merged_lots[lot_id] = {**lot, **existing_lot}  # Keep existing priority data
                        merged_lots[lot_id]['data_sources'] = existing_lot.get('data_sources', []) + [source_name]
                else:
                    # New lot
                    lot['data_sources'] = [source_name]
                    lot['discovery_method'] = f"parallel_{source_name}"
                    merged_lots[lot_id] = lot
        
        return merged_lots
    
    def calculate_data_quality_score(self, lot: Dict) -> float:
        """Calculate data quality score based on available fields and sources"""
        score = 0.0
        
        # Source diversity bonus
        sources = lot.get('data_sources', [])
        score += len(sources) * 10  # 10 points per source
        
        # NextJS real-time data bonus (highest quality)
        if lot.get('has_realtime_data', False):
            score += 25  # Major bonus for real-time NextJS data
        
        # Data source quality bonus
        data_source = lot.get('data_source', '')
        if data_source == 'nextjs_enhanced':
            score += 20  # NextJS enhanced data is highest quality
        elif data_source == 'typesense_fallback':
            score += 15  # Typesense fallback is good quality
        elif data_source == 'typesense_only':
            score += 10  # Typesense only is decent quality
        
        # Essential fields
        essential_fields = ['product_name', 'retail_price', 'current_bid', 'auction_location']
        for field in essential_fields:
            if lot.get(field):
                score += 15
        
        # Detailed fields
        detailed_fields = ['condition_name', 'total_bids', 'unique_bidders', 'expected_close_date']
        for field in detailed_fields:
            if lot.get(field):
                score += 10
        
        # Real-time data bonus
        realtime_fields = ['time_remaining', 'is_open', 'instant_win_price']
        for field in realtime_fields:
            if lot.get(field):
                score += 5
        
        # NextJS specific fields bonus
        nextjs_fields = ['nextjs_current_bid', 'nextjs_total_bids', 'nextjs_unique_bidders', 'nextjs_is_open']
        for field in nextjs_fields:
            if lot.get(field) is not None:
                score += 8
        
        return min(score, 100.0)
    
    async def run_parallel_discovery(self) -> Dict[str, Dict]:
        """Run all discovery systems in parallel for maximum speed"""
        self.discovery_stats['start_time'] = time.time()
        
        self.logger.info("🚀 PARALLEL MULTI-SOURCE DISCOVERY SYSTEM")
        self.logger.info("=" * 60)
        
        # STEP 1: AUTHENTICATE FIRST (MANDATORY)
        self.logger.info("🔐 Step 1: Authentication Required...")
        try:
            self.auth_manager = await require_authentication()
            self.authenticated_headers = get_authenticated_headers()
            customer_id = get_customer_id()
            self.logger.info(f"✅ Authenticated as Customer ID: {customer_id}")
        except Exception as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            raise Exception("Cannot proceed without authentication")
        
        # STEP 2: Initialize discovery systems with authentication
        self.logger.info("🔧 Step 2: Initializing authenticated discovery systems...")
        self.typesense_scanner = TypesenseAllLotsScanner()
        self.nextjs_system = NextJSIntegrationSystem()
        self.warehouse_scanner = ComprehensiveWarehouseScanner()
        
        # Configure systems with authenticated headers
        if hasattr(self.typesense_scanner, 'session') and self.typesense_scanner.session:
            self.typesense_scanner.session.headers.update(self.authenticated_headers)
        if hasattr(self.nextjs_system, 'session') and self.nextjs_system.session:
            self.nextjs_system.session.headers.update(self.authenticated_headers)
        if hasattr(self.warehouse_scanner, 'session') and self.warehouse_scanner.session:
            self.warehouse_scanner.session.headers.update(self.authenticated_headers)
        
        # Pass authenticated headers to systems that need them
        if hasattr(self.typesense_scanner, 'headers'):
            self.typesense_scanner.headers.update(self.authenticated_headers)
        if hasattr(self.nextjs_system, 'headers'):
            self.nextjs_system.headers.update(self.authenticated_headers)
        if hasattr(self.warehouse_scanner, 'headers'):
            self.warehouse_scanner.headers.update(self.authenticated_headers)
        
        self.logger.info("✅ All systems configured with authentication")
        self.logger.info("🚀 Step 3: Running Typesense + NextJS + Warehouse API simultaneously...")
        
        # Run all discovery systems in parallel
        tasks = [
            self.run_typesense_discovery(),
            self.run_nextjs_discovery(),
            self.run_warehouse_discovery()
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"❌ Discovery task failed: {result}")
            else:
                valid_results.append(result)
        
        # Merge all data sources
        self.logger.info("🔄 Merging data from all sources...")
        merged_lots = self.merge_lot_data(valid_results)
        
        # Calculate quality scores
        for lot_id, lot in merged_lots.items():
            lot['data_quality_score'] = self.calculate_data_quality_score(lot)
        
        self.all_discovered_lots = merged_lots
        
        # Update statistics
        self.discovery_stats['end_time'] = time.time()
        self.discovery_stats['total_duration'] = self.discovery_stats['end_time'] - self.discovery_stats['start_time']
        self.discovery_stats['unique_lots_total'] = len(merged_lots)
        self.discovery_stats['data_sources_used'] = len([r for r in valid_results if r[1]])
        
        # Update individual source stats
        for source_name, lots in valid_results:
            if source_name in self.discovery_stats:
                self.discovery_stats[f'{source_name}_lots'] = len(lots)
        
        self.generate_performance_report()
        
        return merged_lots
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        duration = self.discovery_stats['total_duration']
        total_lots = self.discovery_stats['unique_lots_total']
        
        self.logger.info("\n🎯 PARALLEL DISCOVERY PERFORMANCE REPORT")
        self.logger.info("=" * 50)
        self.logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
        self.logger.info(f"📦 Total Unique Lots: {total_lots:,}")
        self.logger.info(f"🚀 Discovery Rate: {total_lots/duration:.1f} lots/second")
        self.logger.info(f"🔗 Data Sources Used: {self.discovery_stats['data_sources_used']}")
        
        self.logger.info("\n📊 SOURCE PERFORMANCE:")
        for source, perf in self.source_performance.items():
            if perf['end'] and perf['start']:
                source_duration = perf['end'] - perf['start']
                self.logger.info(f"   {source.upper()}: {perf['lots']:,} lots in {source_duration:.1f}s ({perf['status']})")
        
        # Quality analysis
        if self.all_discovered_lots:
            quality_scores = [lot.get('data_quality_score', 0) for lot in self.all_discovered_lots.values()]
            avg_quality = sum(quality_scores) / len(quality_scores)
            
            multi_source_lots = len([lot for lot in self.all_discovered_lots.values() 
                                   if len(lot.get('data_sources', [])) > 1])
            
            # NextJS integration analysis
            realtime_count = sum(1 for lot in self.all_discovered_lots.values() if lot.get('has_realtime_data', False))
            nextjs_enhanced = sum(1 for lot in self.all_discovered_lots.values() if lot.get('data_source') == 'nextjs_enhanced')
            typesense_fallback = sum(1 for lot in self.all_discovered_lots.values() if lot.get('data_source') == 'typesense_fallback')
            typesense_only = sum(1 for lot in self.all_discovered_lots.values() if lot.get('data_source') == 'typesense_only')
            
            self.logger.info(f"\n🎯 DATA QUALITY:")
            self.logger.info(f"   Average Quality Score: {avg_quality:.1f}/100")
            self.logger.info(f"   Multi-Source Lots: {multi_source_lots:,} ({multi_source_lots/total_lots*100:.1f}%)")
            
            self.logger.info(f"\n🔄 NEXTJS INTEGRATION STATUS:")
            self.logger.info(f"   Real-time Enhanced: {realtime_count:,} lots ({realtime_count/total_lots*100:.1f}%)")
            self.logger.info(f"   NextJS Enhanced: {nextjs_enhanced:,} lots")
            self.logger.info(f"   Typesense Fallback: {typesense_fallback:,} lots")
            self.logger.info(f"   Typesense Only: {typesense_only:,} lots")
        
        # Speed comparison
        if duration > 0:
            estimated_sequential = sum([
                perf['end'] - perf['start'] for perf in self.source_performance.values() 
                if perf['end'] and perf['start']
            ])
            speedup = estimated_sequential / duration if duration > 0 else 1
            
            self.logger.info(f"\n⚡ SPEED IMPROVEMENT:")
            self.logger.info(f"   Estimated Sequential Time: {estimated_sequential:.1f}s")
            self.logger.info(f"   Actual Parallel Time: {duration:.1f}s")
            self.logger.info(f"   Speed Improvement: {speedup:.1f}x faster!")
    
    def get_top_quality_lots(self, limit: int = 100) -> List[Dict]:
        """Get top lots by data quality score"""
        if not self.all_discovered_lots:
            return []
        
        # Sort by quality score
        sorted_lots = sorted(
            self.all_discovered_lots.values(),
            key=lambda x: x.get('data_quality_score', 0),
            reverse=True
        )
        
        return sorted_lots[:limit]
    
    def get_lots_by_source_combination(self) -> Dict[str, List[Dict]]:
        """Group lots by their source combinations"""
        combinations = {}
        
        for lot in self.all_discovered_lots.values():
            sources = sorted(lot.get('data_sources', []))
            combo_key = '+'.join(sources)
            
            if combo_key not in combinations:
                combinations[combo_key] = []
            combinations[combo_key].append(lot)
        
        return combinations

async def main():
    """Test the parallel discovery system"""
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Testing Parallel Multi-Source Discovery System")
    print("=" * 60)
    
    # Initialize system
    discovery_system = ParallelDiscoverySystem()
    
    # Run parallel discovery
    start_time = time.time()
    merged_lots = await discovery_system.run_parallel_discovery()
    end_time = time.time()
    
    print(f"\n🎉 PARALLEL DISCOVERY COMPLETE!")
    print(f"⏱️  Total Time: {end_time - start_time:.2f} seconds")
    print(f"📦 Total Lots: {len(merged_lots):,}")
    
    # Show top quality lots
    top_lots = discovery_system.get_top_quality_lots(5)
    print(f"\n🏆 TOP 5 HIGHEST QUALITY LOTS:")
    for i, lot in enumerate(top_lots, 1):
        sources = '+'.join(lot.get('data_sources', []))
        quality = lot.get('data_quality_score', 0)
        name = lot.get('product_name') or lot.get('title', 'Unknown')
        price = lot.get('retail_price', 0)
        print(f"   {i}. {name[:50]} (${price:.2f}) - Quality: {quality:.1f} - Sources: {sources}")

if __name__ == "__main__":
    asyncio.run(main()) 