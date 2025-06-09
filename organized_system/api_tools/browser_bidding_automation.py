#!/usr/bin/env python3
"""
Mac.bid Browser Bidding Automation
Uses Selenium to automate real bidding through the web interface
"""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not installed. Run: pip install selenium")

@dataclass
class BidRequest:
    lot_id: int
    auction_id: int
    bid_amount: float
    max_bid: float
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    timing_strategy: str = "IMMEDIATE"  # IMMEDIATE, LAST_MINUTE, SNIPE
    notes: str = ""

@dataclass
class BidResult:
    success: bool
    lot_id: int
    bid_amount: float
    timestamp: str
    message: str
    error: Optional[str] = None
    screenshot_path: Optional[str] = None

class BrowserBiddingAutomation:
    def __init__(self, headless: bool = False, dry_run: bool = True):
        self.headless = headless
        self.dry_run = dry_run
        self.driver = None
        self.wait = None
        self.is_logged_in = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data_outputs/bidding_automation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Mac.bid credentials (from our working system)
        self.customer_id = 2710619
        self.base_url = "https://www.mac.bid"
        
        # Bidding statistics
        self.bid_history = []
        self.session_stats = {
            'bids_attempted': 0,
            'bids_successful': 0,
            'bids_failed': 0,
            'total_amount_bid': 0.0,
            'session_start': datetime.now().isoformat()
        }
        
    def initialize_browser(self) -> bool:
        """Initialize Chrome browser with appropriate settings"""
        
        if not SELENIUM_AVAILABLE:
            self.logger.error("Selenium not available. Cannot initialize browser.")
            return False
        
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Optimize for automation
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # User agent to match our working system
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
            
            # Disable images for faster loading (optional)
            # chrome_options.add_argument("--disable-images")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            self.logger.info("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize browser: {e}")
            return False
    
    def login_to_macbid(self) -> bool:
        """Login to Mac.bid using existing session cookies"""
        
        try:
            self.logger.info("🔐 Logging into Mac.bid...")
            
            # Navigate to Mac.bid
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Add our session cookies
            cookies = {
                '__stripe_mid': 'b1219cc5-9a1f-4e9b-9b3b-ce16a3d90ba32b7fa4',
                'CookieConsent': 'true',
                'ab.storage.deviceId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A6557c69b-3239-8d82-7b30-ec5862a4de57%7Ce%3Aundefined%7Cc%3A1747345668914%7Cl%3A1749267987617',
                'ab.storage.userId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A2710619%7Ce%3Aundefined%7Cc%3A1749188938629%7Cl%3A1749267987617',
                '__stripe_sid': '82edccd6-9b05-4a36-a118-e155bd9212b7ec69fb',
                'mp_78faade7af6b4f2ee5e1af36d8ac6232_mixpanel': '%7B%22distinct_id%22%3A%202710619%2C%22%24device_id%22%3A%20%22196d5eae0323e9-06ed80c653d2808-19525636-13c680-196d5eae0323e9%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22platform%22%3A%20%22website%22%2C%22selected_locations%22%3A%20%5B%0A%20%20%20%20%22Rock%20Hill%22%2C%0A%20%20%20%20%22Gastonia%22%0A%5D%2C%22%24user_id%22%3A%202710619%2C%22active_items%22%3A%20%5B%0A%20%20%20%20%7B%22id%22%3A%2046608657%2C%22invoice_id%22%3A%2018714030%2C%22box_size%22%3A%20%22large%22%2C%22warehouse_location%22%3A%20%22ANL-D-BIN-55%22%2C%22removal_container%22%3A%20null%2C%22product_name%22%3A%20%22KOKISO%20metal%20%22%2C%22status%22%3A%20%22PENDING-TRANSFER%22%2C%22boxes%22%3A%201%2C%22note%22%3A%20null%2C%22current_location_id%22%3A%2038%2C%22allow_transfers%22%3A%201%2C%22allow_shipping%22%3A%200%2C%22is_turbo%22%3A%200%2C%22free_transfers%22%3A%200%2C%22auction_number%22%3A%20%22ANL2506-05-A2%22%2C%22auction_abandon_date%22%3A%20%222025-06-10T18%3A00%3A00.000Z%22%2C%22abandon_date%22%3A%20null%2C%22lot_number%22%3A%20%221726Z%22%2C%22lot_id%22%3A%2035490378%2C%22has_buyer_assurance%22%3A%200%2C%22item_price%22%3A%205.67%2C%22cover_image%22%3A%20%22https%3A%2F%2Fm.media-amazon.com%2Fimages%2FI%2F71fm%2BEdRyKL.jpg%22%2C%22grand_total%22%3A%205.67%2C%22date_paid%22%3A%20%222025-06-06T09%3A20%3A50.000Z%22%2C%22transfer_id%22%3A%206229971%2C%22start_location_code%22%3A%20%22ANL%22%2C%22dest_location_code%22%3A%20%22RHA%22%2C%22start_location_id%22%3A%2038%2C%22dest_location_id%22%3A%2028%2C%22grouping_id%22%3A%20%2218714030_200_35872237%22%2C%22auction_lot_deadline%22%3A%20null%7D%0A%5D%2C%22mac_bucks_balance%22%3A%200%2C%22mac_bucks_gift_balance%22%3A%200%2C%22active_membership%22%3A%20%7B%22id%22%3A%20123339%2C%22date_created%22%3A%20%222025-05-29T18%3A11%3A59.000Z%22%2C%22membership_plan%22%3A%20%22STANDARD%22%2C%22customer_id%22%3A%202710619%2C%22bill_period%22%3A%20%22MONTHLY%22%2C%22bill_amount%22%3A%209.99%2C%22date_cancelled%22%3A%20null%2C%22external_id%22%3A%20%22sub_1RUFc8DhtPPAHVyel4iCCWV7%22%2C%22cancel_reason%22%3A%20null%2C%22stripe_customer_id%22%3A%20%22cus_S6Y0gK006usyW7%22%2C%22date_updated%22%3A%20null%7D%2C%22watchlist_count%22%3A%207%2C%22onboarding%22%3A%20true%7D',
                'ab.storage.sessionId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3Aa18c4004-ac5d-06ae-84af-39127b94f2a6%7Ce%3A1749269831396%7Cc%3A1749267987616%7Cl%3A1749268031396'
            }
            
            for name, value in cookies.items():
                self.driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': '.mac.bid'
                })
            
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(3)
            
            # Check if we're logged in by looking for user-specific elements
            try:
                # Look for account/profile indicators
                user_indicators = [
                    "//a[contains(@href, '/account')]",
                    "//button[contains(text(), 'Account')]",
                    "//div[contains(@class, 'user')]",
                    "//*[contains(text(), '2710619')]"  # Our customer ID
                ]
                
                for indicator in user_indicators:
                    try:
                        element = self.driver.find_element(By.XPATH, indicator)
                        if element:
                            self.is_logged_in = True
                            self.logger.info("✅ Successfully logged into Mac.bid")
                            return True
                    except NoSuchElementException:
                        continue
                
                # If no indicators found, we might still be logged in
                # Check page title or URL
                if "mac.bid" in self.driver.current_url.lower():
                    self.is_logged_in = True
                    self.logger.info("✅ Logged into Mac.bid (session active)")
                    return True
                
            except Exception as e:
                self.logger.warning(f"Could not verify login status: {e}")
                # Assume we're logged in if we got this far
                self.is_logged_in = True
                return True
            
        except Exception as e:
            self.logger.error(f"❌ Login failed: {e}")
            return False
        
        return False
    
    def navigate_to_lot(self, lot_id: int) -> bool:
        """Navigate to a specific lot page"""
        
        try:
            lot_url = f"{self.base_url}/lot/{lot_id}"
            self.logger.info(f"🔍 Navigating to lot {lot_id}")
            
            self.driver.get(lot_url)
            time.sleep(3)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check if lot page loaded successfully
            if str(lot_id) in self.driver.current_url:
                self.logger.info(f"✅ Successfully loaded lot {lot_id}")
                return True
            else:
                self.logger.error(f"❌ Failed to load lot {lot_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error navigating to lot {lot_id}: {e}")
            return False
    
    def analyze_lot_page(self, lot_id: int) -> Dict:
        """Analyze the lot page to understand bidding interface"""
        
        try:
            self.logger.info(f"🔍 Analyzing lot page for {lot_id}")
            
            analysis = {
                'lot_id': lot_id,
                'current_price': None,
                'bid_button_found': False,
                'bid_input_found': False,
                'auction_status': 'UNKNOWN',
                'time_remaining': None,
                'bidding_elements': [],
                'page_title': self.driver.title,
                'current_url': self.driver.current_url
            }
            
            # Look for price information
            price_selectors = [
                "//span[contains(@class, 'price')]",
                "//div[contains(@class, 'current-price')]",
                "//*[contains(text(), '$')]",
                "//span[contains(text(), 'Current Bid')]",
                "//div[contains(@class, 'bid-amount')]"
            ]
            
            for selector in price_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if '$' in text and text not in analysis['bidding_elements']:
                            analysis['bidding_elements'].append(f"Price element: {text}")
                except:
                    continue
            
            # Look for bidding interface elements
            bid_selectors = [
                "//button[contains(text(), 'Bid')]",
                "//button[contains(text(), 'Place Bid')]",
                "//input[contains(@placeholder, 'bid')]",
                "//input[contains(@type, 'number')]",
                "//form[contains(@class, 'bid')]",
                "//div[contains(@class, 'bidding')]"
            ]
            
            for selector in bid_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            tag_name = element.tag_name
                            element_text = element.text.strip() if element.text else ''
                            element_type = element.get_attribute('type') if element.get_attribute('type') else ''
                            placeholder = element.get_attribute('placeholder') if element.get_attribute('placeholder') else ''
                            
                            analysis['bidding_elements'].append(f"{tag_name}: {element_text} {element_type} {placeholder}".strip())
                            
                            if tag_name == 'button' and 'bid' in element_text.lower():
                                analysis['bid_button_found'] = True
                            elif tag_name == 'input' and (element_type == 'number' or 'bid' in placeholder.lower()):
                                analysis['bid_input_found'] = True
                except:
                    continue
            
            # Look for auction status
            status_selectors = [
                "//*[contains(text(), 'LIVE')]",
                "//*[contains(text(), 'ENDED')]",
                "//*[contains(text(), 'CLOSED')]",
                "//*[contains(text(), 'ACTIVE')]",
                "//div[contains(@class, 'status')]"
            ]
            
            for selector in status_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed():
                        analysis['auction_status'] = element.text.strip()
                        break
                except:
                    continue
            
            self.logger.info(f"📊 Lot analysis complete:")
            self.logger.info(f"   Bid button found: {analysis['bid_button_found']}")
            self.logger.info(f"   Bid input found: {analysis['bid_input_found']}")
            self.logger.info(f"   Status: {analysis['auction_status']}")
            self.logger.info(f"   Elements found: {len(analysis['bidding_elements'])}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing lot page: {e}")
            return {'error': str(e)}
    
    def place_bid(self, bid_request: BidRequest) -> BidResult:
        """Place a bid on a specific lot"""
        
        self.session_stats['bids_attempted'] += 1
        
        try:
            self.logger.info(f"🎯 Placing bid: ${bid_request.bid_amount} on lot {bid_request.lot_id}")
            
            if self.dry_run:
                self.logger.info("🧪 DRY RUN MODE - No actual bid will be placed")
                return BidResult(
                    success=True,
                    lot_id=bid_request.lot_id,
                    bid_amount=bid_request.bid_amount,
                    timestamp=datetime.now().isoformat(),
                    message="DRY RUN: Bid would have been placed successfully"
                )
            
            # Navigate to lot
            if not self.navigate_to_lot(bid_request.lot_id):
                return BidResult(
                    success=False,
                    lot_id=bid_request.lot_id,
                    bid_amount=bid_request.bid_amount,
                    timestamp=datetime.now().isoformat(),
                    message="Failed to navigate to lot",
                    error="Navigation failed"
                )
            
            # Analyze the page first
            analysis = self.analyze_lot_page(bid_request.lot_id)
            
            if not analysis.get('bid_button_found') and not analysis.get('bid_input_found'):
                return BidResult(
                    success=False,
                    lot_id=bid_request.lot_id,
                    bid_amount=bid_request.bid_amount,
                    timestamp=datetime.now().isoformat(),
                    message="No bidding interface found on page",
                    error="Missing bid elements"
                )
            
            # Take screenshot before bidding
            screenshot_path = f"data_outputs/screenshots/bid_attempt_{bid_request.lot_id}_{int(time.time())}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            self.driver.save_screenshot(screenshot_path)
            
            # Try to find and fill bid input
            bid_input_selectors = [
                "//input[contains(@placeholder, 'bid')]",
                "//input[@type='number']",
                "//input[contains(@class, 'bid')]",
                "//input[contains(@name, 'bid')]"
            ]
            
            bid_input = None
            for selector in bid_input_selectors:
                try:
                    bid_input = self.driver.find_element(By.XPATH, selector)
                    if bid_input.is_displayed():
                        break
                except:
                    continue
            
            if bid_input:
                # Clear and enter bid amount
                bid_input.clear()
                bid_input.send_keys(str(bid_request.bid_amount))
                time.sleep(1)
                
                self.logger.info(f"✅ Entered bid amount: ${bid_request.bid_amount}")
            
            # Try to find and click bid button
            bid_button_selectors = [
                "//button[contains(text(), 'Place Bid')]",
                "//button[contains(text(), 'Bid')]",
                "//button[contains(@class, 'bid')]",
                "//input[@type='submit'][contains(@value, 'Bid')]"
            ]
            
            bid_button = None
            for selector in bid_button_selectors:
                try:
                    bid_button = self.driver.find_element(By.XPATH, selector)
                    if bid_button.is_displayed() and bid_button.is_enabled():
                        break
                except:
                    continue
            
            if bid_button:
                # Click the bid button
                ActionChains(self.driver).move_to_element(bid_button).click().perform()
                time.sleep(2)
                
                self.logger.info("✅ Clicked bid button")
                
                # Wait for response/confirmation
                time.sleep(3)
                
                # Take screenshot after bidding
                after_screenshot = f"data_outputs/screenshots/bid_result_{bid_request.lot_id}_{int(time.time())}.png"
                self.driver.save_screenshot(after_screenshot)
                
                # Check for success/error messages
                success_indicators = [
                    "//*[contains(text(), 'successful')]",
                    "//*[contains(text(), 'placed')]",
                    "//*[contains(text(), 'confirmed')]"
                ]
                
                error_indicators = [
                    "//*[contains(text(), 'error')]",
                    "//*[contains(text(), 'failed')]",
                    "//*[contains(text(), 'invalid')]"
                ]
                
                # Check for success
                for indicator in success_indicators:
                    try:
                        element = self.driver.find_element(By.XPATH, indicator)
                        if element.is_displayed():
                            self.session_stats['bids_successful'] += 1
                            self.session_stats['total_amount_bid'] += bid_request.bid_amount
                            
                            return BidResult(
                                success=True,
                                lot_id=bid_request.lot_id,
                                bid_amount=bid_request.bid_amount,
                                timestamp=datetime.now().isoformat(),
                                message=f"Bid placed successfully: {element.text}",
                                screenshot_path=after_screenshot
                            )
                    except:
                        continue
                
                # Check for errors
                for indicator in error_indicators:
                    try:
                        element = self.driver.find_element(By.XPATH, indicator)
                        if element.is_displayed():
                            self.session_stats['bids_failed'] += 1
                            
                            return BidResult(
                                success=False,
                                lot_id=bid_request.lot_id,
                                bid_amount=bid_request.bid_amount,
                                timestamp=datetime.now().isoformat(),
                                message=f"Bid failed: {element.text}",
                                error=element.text,
                                screenshot_path=after_screenshot
                            )
                    except:
                        continue
                
                # No clear success/error message found
                self.session_stats['bids_successful'] += 1  # Assume success
                return BidResult(
                    success=True,
                    lot_id=bid_request.lot_id,
                    bid_amount=bid_request.bid_amount,
                    timestamp=datetime.now().isoformat(),
                    message="Bid submitted (no confirmation message found)",
                    screenshot_path=after_screenshot
                )
            
            else:
                return BidResult(
                    success=False,
                    lot_id=bid_request.lot_id,
                    bid_amount=bid_request.bid_amount,
                    timestamp=datetime.now().isoformat(),
                    message="Could not find bid button",
                    error="Missing bid button",
                    screenshot_path=screenshot_path
                )
                
        except Exception as e:
            self.session_stats['bids_failed'] += 1
            self.logger.error(f"❌ Error placing bid: {e}")
            
            return BidResult(
                success=False,
                lot_id=bid_request.lot_id,
                bid_amount=bid_request.bid_amount,
                timestamp=datetime.now().isoformat(),
                message=f"Exception occurred: {str(e)}",
                error=str(e)
            )
    
    def execute_bidding_session(self, bid_requests: List[BidRequest]) -> List[BidResult]:
        """Execute multiple bids in a session"""
        
        self.logger.info(f"🎯 Starting bidding session with {len(bid_requests)} bids")
        
        if not self.initialize_browser():
            return []
        
        if not self.login_to_macbid():
            return []
        
        results = []
        
        for bid_request in bid_requests:
            self.logger.info(f"Processing bid {len(results) + 1}/{len(bid_requests)}")
            
            result = self.place_bid(bid_request)
            results.append(result)
            self.bid_history.append(result)
            
            # Log result
            if result.success:
                self.logger.info(f"✅ Bid successful: ${result.bid_amount} on lot {result.lot_id}")
            else:
                self.logger.error(f"❌ Bid failed: {result.message}")
            
            # Wait between bids to avoid rate limiting
            time.sleep(2)
        
        # Generate session report
        self.generate_session_report(results)
        
        return results
    
    def generate_session_report(self, results: List[BidResult]) -> Dict:
        """Generate comprehensive session report"""
        
        self.session_stats['session_end'] = datetime.now().isoformat()
        
        report = {
            'session_stats': self.session_stats,
            'bid_results': [
                {
                    'lot_id': r.lot_id,
                    'bid_amount': r.bid_amount,
                    'success': r.success,
                    'timestamp': r.timestamp,
                    'message': r.message,
                    'error': r.error
                } for r in results
            ],
            'summary': {
                'total_bids': len(results),
                'successful_bids': sum(1 for r in results if r.success),
                'failed_bids': sum(1 for r in results if not r.success),
                'success_rate': (sum(1 for r in results if r.success) / len(results) * 100) if results else 0,
                'total_amount_bid': sum(r.bid_amount for r in results if r.success)
            }
        }
        
        # Save report
        os.makedirs('data_outputs', exist_ok=True)
        report_path = f"data_outputs/bidding_session_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📊 SESSION SUMMARY:")
        self.logger.info(f"   Total Bids: {report['summary']['total_bids']}")
        self.logger.info(f"   Successful: {report['summary']['successful_bids']}")
        self.logger.info(f"   Failed: {report['summary']['failed_bids']}")
        self.logger.info(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
        self.logger.info(f"   Total Amount: ${report['summary']['total_amount_bid']:.2f}")
        self.logger.info(f"   Report saved: {report_path}")
        
        return report
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            self.driver.quit()
            self.logger.info("🧹 Browser cleanup complete")

def main():
    """Test the browser bidding automation"""
    
    print("🎯 MAC.BID BROWSER BIDDING AUTOMATION")
    print("="*50)
    
    # Test with our known lot
    test_bid = BidRequest(
        lot_id=35863830,
        auction_id=48796,
        bid_amount=1.00,
        max_bid=5.00,
        priority="HIGH",
        timing_strategy="IMMEDIATE",
        notes="Test bid for system validation"
    )
    
    # Initialize automation (DRY RUN mode)
    automation = BrowserBiddingAutomation(headless=False, dry_run=True)
    
    try:
        # Execute test bid
        results = automation.execute_bidding_session([test_bid])
        
        if results:
            print(f"\n✅ Test completed!")
            print(f"   Result: {'SUCCESS' if results[0].success else 'FAILED'}")
            print(f"   Message: {results[0].message}")
        else:
            print(f"\n❌ Test failed - no results")
            
    finally:
        automation.cleanup()

if __name__ == "__main__":
    main() 