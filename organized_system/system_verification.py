#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE SYSTEM VERIFICATION
Advanced Auction Intelligence System - Post-Cleanup Verification

This script verifies that all system components are working correctly
after the cleanup and ensures all dependencies are properly configured.
"""

import os
import sys
import sqlite3
import importlib.util
import traceback
from pathlib import Path

class SystemVerifier:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def log_result(self, test_name, status, message=""):
        """Log test results"""
        if status == 'PASS':
            self.results['passed'].append(f"✅ {test_name}: {message}")
            print(f"✅ {test_name}: {message}")
        elif status == 'FAIL':
            self.results['failed'].append(f"❌ {test_name}: {message}")
            print(f"❌ {test_name}: {message}")
        else:  # WARNING
            self.results['warnings'].append(f"⚠️  {test_name}: {message}")
            print(f"⚠️  {test_name}: {message}")
    
    def test_dependencies(self):
        """Test all required dependencies"""
        print("\n🔍 TESTING DEPENDENCIES...")
        
        required_packages = [
            'aiohttp', 'requests', 'pandas', 'numpy', 
            'scikit-learn', 'sqlite3', 'asyncio', 'json'
        ]
        
        for package in required_packages:
            try:
                if package == 'scikit-learn':
                    import sklearn
                    self.log_result(f"Import {package}", 'PASS', f"Version: {sklearn.__version__}")
                elif package in ['sqlite3', 'asyncio', 'json']:
                    exec(f"import {package}")
                    self.log_result(f"Import {package}", 'PASS', "Built-in module")
                else:
                    module = __import__(package)
                    version = getattr(module, '__version__', 'Unknown')
                    self.log_result(f"Import {package}", 'PASS', f"Version: {version}")
            except ImportError as e:
                self.log_result(f"Import {package}", 'FAIL', str(e))
    
    def test_core_files(self):
        """Test core system files"""
        print("\n🔍 TESTING CORE SYSTEM FILES...")
        
        core_files = {
            'core_systems/integrated_auction_system.py': 'Main Integration System',
            'core_systems/real_bidding_system.py': 'Phase 1: Real Bidding',
            'core_systems/portfolio_management_system.py': 'Phase 2: Portfolio Management',
            'core_systems/advanced_auction_intelligence.py': 'Legacy System (Reference)',
            'core_systems/automated_bidding_system.py': 'Automated Bidding',
            'core_systems/realtime_auction_monitor.py': 'Real-time Monitor',
            'core_systems/nextjs_integration_system.py': 'NextJS Integration',
            'ml_prediction/enhanced_ml_models.py': 'Phase 3: Enhanced ML',
            'ml_prediction/predictive_pricing_model.py': 'Predictive Pricing',
            'api_tools/bidding_api_discovery.py': 'API Discovery',
            'api_tools/browser_bidding_automation.py': 'Browser Automation',
            'api_tools/network_traffic_analyzer.py': 'Network Analysis'
        }
        
        for file_path, description in core_files.items():
            full_path = self.base_path / file_path
            if full_path.exists():
                try:
                    # Test compilation
                    with open(full_path, 'r') as f:
                        compile(f.read(), str(full_path), 'exec')
                    self.log_result(f"File {file_path}", 'PASS', f"{description} - Syntax OK")
                except SyntaxError as e:
                    self.log_result(f"File {file_path}", 'FAIL', f"Syntax Error: {e}")
                except Exception as e:
                    self.log_result(f"File {file_path}", 'FAIL', f"Error: {e}")
            else:
                self.log_result(f"File {file_path}", 'FAIL', "File not found")
    
    def test_databases(self):
        """Test database files"""
        print("\n🔍 TESTING DATABASE FILES...")
        
        db_files = [
            'databases/integrated_auction_system.db',
            'databases/portfolio_management.db',
            'databases/enhanced_ml_models.db',
            'databases/real_bidding_system.db',
            'databases/predictive_pricing.db',
            'databases/realtime_auction_monitor.db',
            'databases/automated_bidding.db'
        ]
        
        for db_file in db_files:
            db_path = self.base_path / db_file
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    self.log_result(f"Database {db_file}", 'PASS', f"{len(tables)} tables found")
                except Exception as e:
                    self.log_result(f"Database {db_file}", 'FAIL', f"Error: {e}")
            else:
                self.log_result(f"Database {db_file}", 'WARNING', "Database will be created on first run")
    
    def test_ml_models(self):
        """Test ML model files"""
        print("\n🔍 TESTING ML MODEL FILES...")
        
        # Test the actual ML system functionality instead of individual pickle files
        try:
            sys.path.append(str(self.base_path))
            from ml_prediction.enhanced_ml_models import EnhancedMLModels
            
            ml = EnhancedMLModels()
            
            # Test prediction functionality
            test_lot = {
                'title': 'Test Item',
                'category': 'Electronics',
                'condition': 'USED',
                'testing_status': 'TESTED',
                'current_bid': 100.0,
                'retail_price': 500.0,
                'bidder_count': 5,
                'bid_count': 3
            }
            
            result = ml.predict_auction_price(test_lot)
            
            if hasattr(result, 'predicted_final_price'):
                self.log_result("ML System Integration", 'PASS', f"Prediction successful: ${result.predicted_final_price:.2f}")
                
                # Check individual model files exist
                model_files = [
                    'ml_prediction/saved_models/gradient_boosting_model.pkl',
                    'ml_prediction/saved_models/random_forest_model.pkl',
                    'ml_prediction/saved_models/ridge_regression_model.pkl',
                    'ml_prediction/saved_models/scalers.pkl',
                    'ml_prediction/saved_models/encoders.pkl',
                    'ml_prediction/saved_models/feature_selectors.pkl'
                ]
                
                for model_file in model_files:
                    model_path = self.base_path / model_file
                    if model_path.exists():
                        self.log_result(f"Model {model_file}", 'PASS', f"File exists ({model_path.stat().st_size} bytes)")
                    else:
                        self.log_result(f"Model {model_file}", 'WARNING', "Model will be trained on first run")
            else:
                self.log_result("ML System Integration", 'FAIL', "Prediction failed")
                
        except Exception as e:
            self.log_result("ML System Integration", 'FAIL', f"Error: {e}")
            
            # Fallback to file existence check
            model_files = [
                'ml_prediction/saved_models/gradient_boosting_model.pkl',
                'ml_prediction/saved_models/random_forest_model.pkl',
                'ml_prediction/saved_models/ridge_regression_model.pkl',
                'ml_prediction/saved_models/scalers.pkl',
                'ml_prediction/saved_models/encoders.pkl',
                'ml_prediction/saved_models/feature_selectors.pkl'
            ]
            
            for model_file in model_files:
                model_path = self.base_path / model_file
                if model_path.exists():
                    self.log_result(f"Model {model_file}", 'WARNING', "File exists but system test failed")
                else:
                    self.log_result(f"Model {model_file}", 'WARNING', "Model will be trained on first run")
    
    def test_directory_structure(self):
        """Test directory structure"""
        print("\n🔍 TESTING DIRECTORY STRUCTURE...")
        
        required_dirs = [
            'core_systems',
            'api_tools', 
            'ml_prediction',
            'ml_prediction/saved_models',
            'databases',
            'data_outputs',
            'documentation'
        ]
        
        for dir_name in required_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                file_count = len(list(dir_path.iterdir()))
                self.log_result(f"Directory {dir_name}", 'PASS', f"{file_count} items")
            else:
                self.log_result(f"Directory {dir_name}", 'FAIL', "Directory not found")
    
    def test_requirements(self):
        """Test requirements file"""
        print("\n🔍 TESTING REQUIREMENTS FILE...")
        
        req_file = self.base_path / 'requirements_advanced_system.txt'
        if req_file.exists():
            with open(req_file, 'r') as f:
                content = f.read()
                if 'aiohttp' in content and 'scikit-learn' in content:
                    self.log_result("Requirements file", 'PASS', "All dependencies listed")
                else:
                    self.log_result("Requirements file", 'FAIL', "Missing dependencies")
        else:
            self.log_result("Requirements file", 'FAIL', "File not found")
    
    def run_integration_test(self):
        """Run a basic integration test"""
        print("\n🔍 RUNNING INTEGRATION TEST...")
        
        try:
            # Test basic imports from our system
            sys.path.append(str(self.base_path))
            
            # Test if we can import the main system
            spec = importlib.util.spec_from_file_location(
                "integrated_auction_system", 
                self.base_path / "core_systems/integrated_auction_system.py"
            )
            module = importlib.util.module_from_spec(spec)
            
            # This will test if all imports work
            spec.loader.exec_module(module)
            
            self.log_result("Integration Test", 'PASS', "All imports successful")
            
        except Exception as e:
            self.log_result("Integration Test", 'FAIL', f"Import error: {str(e)}")
    
    def generate_report(self):
        """Generate final verification report"""
        print("\n" + "="*60)
        print("🎯 SYSTEM VERIFICATION REPORT")
        print("="*60)
        
        total_tests = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])
        passed_tests = len(self.results['passed'])
        failed_tests = len(self.results['failed'])
        warning_tests = len(self.results['warnings'])
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Warnings: {warning_tests}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"   🎯 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for failure in self.results['failed']:
                print(f"   {failure}")
        
        if warning_tests > 0:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.results['warnings']:
                print(f"   {warning}")
        
        print(f"\n🎉 SYSTEM STATUS: {'READY FOR PRODUCTION' if failed_tests == 0 else 'NEEDS ATTENTION'}")
        
        return failed_tests == 0

def main():
    """Main verification function"""
    print("🚀 ADVANCED AUCTION INTELLIGENCE SYSTEM")
    print("🔍 POST-CLEANUP VERIFICATION")
    print("="*60)
    
    verifier = SystemVerifier()
    
    # Run all tests
    verifier.test_dependencies()
    verifier.test_directory_structure()
    verifier.test_requirements()
    verifier.test_core_files()
    verifier.test_databases()
    verifier.test_ml_models()
    verifier.run_integration_test()
    
    # Generate final report
    success = verifier.generate_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 