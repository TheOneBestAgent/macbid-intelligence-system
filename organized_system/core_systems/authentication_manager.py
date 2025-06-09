#!/usr/bin/env python3
"""
🔐 Authentication Manager for Mac.bid
Centralized authentication system that all scripts must use before starting operations
"""

import os
import json
import time
import logging
import aiohttp
import asyncio
from typing import Dict, Optional, Tuple
from pathlib import Path

class MacBidAuthenticationManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Authentication credentials
        self.customer_id = "2710619"  # Your Mac.bid customer ID
        self.jwt_token = None
        self.session_cookies = {}
        self.auth_headers = {}
        
        # Authentication status
        self.is_authenticated = False
        self.auth_timestamp = None
        self.auth_expiry = None
        
        # File paths
        self.credentials_dir = Path.home() / ".macbid_scraper"
        self.tokens_file = self.credentials_dir / "api_tokens.json"
        self.session_file = self.credentials_dir / "authenticated_session.json"
        
        # Ensure credentials directory exists
        self.credentials_dir.mkdir(exist_ok=True)
        
        # Standard headers for Mac.bid
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    def load_stored_credentials(self) -> bool:
        """Load stored authentication credentials"""
        try:
            # Try to load JWT token
            if self.tokens_file.exists():
                with open(self.tokens_file, 'r') as f:
                    token_data = json.load(f)
                    self.jwt_token = token_data.get('tokens', {}).get('authorization')
                    stored_customer_id = token_data.get('customer_id')
                    
                    if stored_customer_id and stored_customer_id != self.customer_id:
                        self.logger.warning(f"Customer ID mismatch: stored {stored_customer_id}, expected {self.customer_id}")
                    
                    if self.jwt_token:
                        self.logger.info(f"✅ Loaded JWT token: {self.jwt_token[:50]}...")
            
            # Try to load session cookies
            if self.session_file.exists():
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                    cookies = session_data.get('cookies', [])
                    
                    # Convert cookies to dict
                    for cookie in cookies:
                        if cookie.get('domain') in ['.mac.bid', 'mac.bid', 'www.mac.bid']:
                            self.session_cookies[cookie['name']] = cookie['value']
                    
                    self.logger.info(f"✅ Loaded {len(self.session_cookies)} session cookies")
            
            # Check if we have minimum required auth
            if self.jwt_token and self.customer_id:
                self.is_authenticated = True
                self.auth_timestamp = time.time()
                self.logger.info("✅ Authentication credentials loaded successfully")
                return True
            else:
                self.logger.warning("⚠️ Incomplete authentication credentials")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error loading credentials: {e}")
            return False
    
    def setup_authenticated_headers(self) -> Dict[str, str]:
        """Setup headers with authentication"""
        headers = self.base_headers.copy()
        
        if self.jwt_token:
            headers.update({
                'authorization': self.jwt_token,
                'origin': 'https://www.mac.bid',
                'referer': 'https://www.mac.bid/'
            })
        
        # Add session cookies if available
        if self.session_cookies:
            cookie_string = '; '.join([f"{k}={v}" for k, v in self.session_cookies.items()])
            headers['Cookie'] = cookie_string
        
        self.auth_headers = headers
        return headers
    
    async def verify_authentication(self) -> bool:
        """Verify that authentication is working"""
        if not self.is_authenticated:
            return False
        
        try:
            # Test authentication with a simple API call
            async with aiohttp.ClientSession() as session:
                # Try to access customer-specific endpoint
                test_url = f"https://api.macdiscount.com/auctions/customer/{self.customer_id}/active-auctions"
                
                async with session.get(test_url, headers=self.auth_headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info("✅ Authentication verified successfully")
                        return True
                    elif response.status == 401:
                        self.logger.error("❌ Authentication failed: Invalid credentials")
                        self.is_authenticated = False
                        return False
                    else:
                        self.logger.warning(f"⚠️ Authentication test returned status {response.status}")
                        return True  # Assume OK for non-401 errors
                        
        except Exception as e:
            self.logger.error(f"❌ Error verifying authentication: {e}")
            return False
    
    async def ensure_authentication(self) -> bool:
        """Ensure authentication is valid before proceeding"""
        self.logger.info("🔐 AUTHENTICATION MANAGER")
        self.logger.info("=" * 40)
        
        # Step 1: Load stored credentials
        self.logger.info("📂 Loading stored credentials...")
        if not self.load_stored_credentials():
            self.logger.error("❌ Failed to load authentication credentials")
            self.logger.error("💡 Please ensure you have valid credentials in:")
            self.logger.error(f"   - {self.tokens_file}")
            self.logger.error(f"   - {self.session_file}")
            return False
        
        # Step 2: Setup authenticated headers
        self.logger.info("🔧 Setting up authenticated headers...")
        self.setup_authenticated_headers()
        
        # Step 3: Verify authentication works
        self.logger.info("🔍 Verifying authentication...")
        if not await self.verify_authentication():
            self.logger.error("❌ Authentication verification failed")
            return False
        
        self.logger.info("✅ AUTHENTICATION SUCCESSFUL")
        self.logger.info(f"👤 Customer ID: {self.customer_id}")
        self.logger.info(f"🔑 JWT Token: {self.jwt_token[:50] if self.jwt_token else 'None'}...")
        self.logger.info(f"🍪 Session Cookies: {len(self.session_cookies)} loaded")
        self.logger.info("=" * 40)
        
        return True
    
    def get_authenticated_session_config(self) -> Dict:
        """Get configuration for authenticated HTTP sessions"""
        return {
            'headers': self.auth_headers,
            'cookies': self.session_cookies,
            'customer_id': self.customer_id,
            'jwt_token': self.jwt_token
        }
    
    def save_credentials(self, jwt_token: str = None, cookies: Dict = None):
        """Save authentication credentials for future use"""
        try:
            # Save JWT token
            if jwt_token:
                self.jwt_token = jwt_token
                token_data = {
                    'customer_id': self.customer_id,
                    'tokens': {
                        'authorization': jwt_token
                    },
                    'timestamp': time.time()
                }
                
                with open(self.tokens_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                self.logger.info(f"✅ JWT token saved to {self.tokens_file}")
            
            # Save session cookies
            if cookies:
                self.session_cookies.update(cookies)
                session_data = {
                    'customer_id': self.customer_id,
                    'cookies': [
                        {
                            'name': name,
                            'value': value,
                            'domain': '.mac.bid'
                        }
                        for name, value in cookies.items()
                    ],
                    'timestamp': time.time()
                }
                
                with open(self.session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                
                self.logger.info(f"✅ Session cookies saved to {self.session_file}")
                
        except Exception as e:
            self.logger.error(f"❌ Error saving credentials: {e}")
    
    def is_auth_expired(self) -> bool:
        """Check if authentication has expired"""
        if not self.auth_timestamp:
            return True
        
        # Consider auth expired after 24 hours
        return (time.time() - self.auth_timestamp) > (24 * 60 * 60)
    
    def get_auth_status(self) -> Dict:
        """Get current authentication status"""
        return {
            'is_authenticated': self.is_authenticated,
            'customer_id': self.customer_id,
            'has_jwt_token': bool(self.jwt_token),
            'has_session_cookies': bool(self.session_cookies),
            'auth_timestamp': self.auth_timestamp,
            'is_expired': self.is_auth_expired(),
            'headers_configured': bool(self.auth_headers)
        }

# Global authentication manager instance
auth_manager = MacBidAuthenticationManager()

async def require_authentication() -> MacBidAuthenticationManager:
    """
    Decorator/function to ensure authentication before any Mac.bid operations
    This MUST be called at the start of every script
    """
    if not await auth_manager.ensure_authentication():
        raise Exception("❌ AUTHENTICATION REQUIRED: Cannot proceed without valid Mac.bid authentication")
    
    return auth_manager

def get_authenticated_headers() -> Dict[str, str]:
    """Get authenticated headers for HTTP requests"""
    if not auth_manager.is_authenticated:
        raise Exception("❌ Not authenticated. Call require_authentication() first.")
    
    return auth_manager.auth_headers

def get_customer_id() -> str:
    """Get the authenticated customer ID"""
    if not auth_manager.is_authenticated:
        raise Exception("❌ Not authenticated. Call require_authentication() first.")
    
    return auth_manager.customer_id

async def main():
    """Test authentication manager"""
    logging.basicConfig(level=logging.INFO)
    
    print("🔐 Testing Mac.bid Authentication Manager")
    print("=" * 50)
    
    try:
        # Test authentication
        auth = await require_authentication()
        
        print("\n📊 Authentication Status:")
        status = auth.get_auth_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Authentication test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Authentication test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 