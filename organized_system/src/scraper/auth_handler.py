"""Authentication handler for accessing protected API endpoints."""

import asyncio
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page, Browser
import requests
from bs4 import BeautifulSoup

from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class AuthCredentials:
    """Container for authentication credentials."""
    username: str
    password: str
    auth_type: str = "form"  # form, basic, bearer, custom
    login_url: Optional[str] = None
    username_field: str = "username"
    password_field: str = "password"
    submit_selector: str = "input[type=submit], button[type=submit], button"
    success_indicators: List[str] = None
    additional_fields: Dict[str, str] = None

    def __post_init__(self):
        if self.success_indicators is None:
            self.success_indicators = ["dashboard", "profile", "logout", "welcome"]
        if self.additional_fields is None:
            self.additional_fields = {}


class AuthHandler:
    """Handle various authentication methods for web scraping."""
    
    def __init__(self):
        self.session = requests.Session()
        self.authenticated = False
        self.auth_cookies = {}
        self.auth_headers = {}
    
    async def authenticate_static(self, credentials: AuthCredentials, base_url: str) -> bool:
        """Authenticate using static HTTP requests (for simple form auth)."""
        try:
            if credentials.auth_type == "basic":
                return self._authenticate_basic(credentials)
            elif credentials.auth_type == "bearer":
                return self._authenticate_bearer(credentials)
            elif credentials.auth_type == "form":
                return await self._authenticate_form_static(credentials, base_url)
            else:
                logger.error(f"Unsupported auth type for static auth: {credentials.auth_type}")
                return False
        except Exception as e:
            logger.error(f"Static authentication failed: {e}")
            return False
    
    async def authenticate_dynamic(self, credentials: AuthCredentials, page: Page, base_url: str) -> bool:
        """Authenticate using browser automation (for complex forms, 2FA, etc.)."""
        try:
            if credentials.auth_type == "form":
                return await self._authenticate_form_dynamic(credentials, page, base_url)
            else:
                logger.error(f"Unsupported auth type for dynamic auth: {credentials.auth_type}")
                return False
        except Exception as e:
            logger.error(f"Dynamic authentication failed: {e}")
            return False
    
    def _authenticate_basic(self, credentials: AuthCredentials) -> bool:
        """Set up HTTP Basic Authentication."""
        self.session.auth = (credentials.username, credentials.password)
        self.authenticated = True
        logger.info("HTTP Basic Authentication configured")
        return True
    
    def _authenticate_bearer(self, credentials: AuthCredentials) -> bool:
        """Set up Bearer token authentication."""
        # In this case, we expect the password field to contain the token
        token = credentials.password
        self.auth_headers['Authorization'] = f'Bearer {token}'
        self.session.headers.update(self.auth_headers)
        self.authenticated = True
        logger.info("Bearer token authentication configured")
        return True
    
    async def _authenticate_form_static(self, credentials: AuthCredentials, base_url: str) -> bool:
        """Authenticate using form submission with requests."""
        login_url = credentials.login_url or self._find_login_url(base_url)
        if not login_url:
            logger.error("Could not determine login URL")
            return False
        
        # Get the login page to extract any CSRF tokens or hidden fields
        login_response = self.session.get(login_url)
        if login_response.status_code != 200:
            logger.error(f"Failed to access login page: {login_response.status_code}")
            return False
        
        # Parse the login form
        soup = BeautifulSoup(login_response.text, 'html.parser')
        form = soup.find('form')
        if not form:
            logger.error("No form found on login page")
            return False
        
        # Build form data
        form_data = {}
        
        # Add hidden fields (like CSRF tokens)
        for hidden_input in form.find_all('input', type='hidden'):
            name = hidden_input.get('name')
            value = hidden_input.get('value', '')
            if name:
                form_data[name] = value
        
        # Add credentials
        form_data[credentials.username_field] = credentials.username
        form_data[credentials.password_field] = credentials.password
        
        # Add any additional fields
        form_data.update(credentials.additional_fields)
        
        # Determine form action
        form_action = form.get('action', '')
        if form_action:
            submit_url = urljoin(login_url, form_action)
        else:
            submit_url = login_url
        
        # Submit the form
        method = form.get('method', 'POST').upper()
        if method == 'POST':
            auth_response = self.session.post(submit_url, data=form_data)
        else:
            auth_response = self.session.get(submit_url, params=form_data)
        
        # Check if authentication was successful
        success = self._check_auth_success(auth_response, credentials.success_indicators)
        if success:
            self.authenticated = True
            self.auth_cookies = dict(self.session.cookies)
            logger.info("Form authentication successful")
        else:
            logger.error("Form authentication failed")
        
        return success
    
    async def _authenticate_form_dynamic(self, credentials: AuthCredentials, page: Page, base_url: str) -> bool:
        """Authenticate using browser automation for complex forms."""
        login_url = credentials.login_url or base_url
        
        logger.info(f"Attempting to authenticate at: {login_url}")
        
        # Navigate to the page (could be main page or login page)
        await page.goto(login_url, wait_until='domcontentloaded')
        
        # Wait for JavaScript to load
        await asyncio.sleep(5)
        
        # Check if we need to click a "Log In" button to show the form
        login_form_visible = await page.query_selector('input[name="password"], input[type="password"]')
        if not login_form_visible:
            logger.info("Login form not visible, looking for Log In button...")
            
            # Try to find and click the Log In button
            login_button_selectors = [
                'button:has-text("Log In")',
                'button:has-text("Login")',
                'a:has-text("Log In")',
                'a:has-text("Login")',
                '.login-button',
                '[data-testid*="login"]'
            ]
            
            clicked_login = False
            for selector in login_button_selectors:
                try:
                    login_button = await page.query_selector(selector)
                    if login_button:
                        await login_button.click()
                        clicked_login = True
                        logger.info(f"Clicked login button with selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to click login button with selector {selector}: {e}")
            
            if clicked_login:
                # Wait for the login form to appear
                await asyncio.sleep(3)
            else:
                logger.warning("Could not find or click Log In button")
        
        # Wait for login form elements to be present
        try:
            await page.wait_for_selector('input[type="password"], input[name="password"], #password', timeout=10000)
        except Exception as e:
            logger.debug(f"Password field not found: {e}")
            # Continue anyway, might be a different form structure
        
        # Fill in username
        username_selectors = [
            f'input[name="{credentials.username_field}"]',
            f'#{credentials.username_field}',
            'input[name="email"]',  # Common for mac.bid
            '#si-email',  # Specific for mac.bid
            'input[type="email"]',
            'input[type="text"]',
            'input[placeholder*="username" i]',
            'input[placeholder*="email" i]',
            'input[placeholder*="user" i]',
            'input[autocomplete="username"]',
            'input[autocomplete="email"]',
            '[data-testid*="username"]',
            '[data-testid*="email"]',
            '.username input',
            '.email input',
            '.login-username',
            '.login-email'
        ]
        
        username_filled = False
        for selector in username_selectors:
            try:
                # Wait for the element to be available
                await page.wait_for_selector(selector, timeout=3000)
                username_input = await page.query_selector(selector)
                if username_input:
                    # Clear any existing content and fill
                    await username_input.click()
                    await username_input.fill('')
                    await asyncio.sleep(0.5)
                    await username_input.type(credentials.username, delay=50)
                    username_filled = True
                    logger.debug(f"Filled username using selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Failed to fill username with selector {selector}: {e}")
        
        if not username_filled:
            logger.error("Could not find username field")
            return False
        
        # Fill in password
        password_selectors = [
            f'input[name="{credentials.password_field}"]',
            f'#{credentials.password_field}',
            'input[name="password"]',  # Common for mac.bid
            '#si-password',  # Specific for mac.bid
            'input[type="password"]',
            'input[placeholder*="password" i]',
            'input[autocomplete="current-password"]',
            'input[autocomplete="password"]',
            '[data-testid*="password"]',
            '.password input',
            '.login-password'
        ]
        
        password_filled = False
        for selector in password_selectors:
            try:
                # Wait for the element to be available
                await page.wait_for_selector(selector, timeout=3000)
                password_input = await page.query_selector(selector)
                if password_input:
                    # Clear any existing content and fill
                    await password_input.click()
                    await password_input.fill('')
                    await asyncio.sleep(0.5)
                    await password_input.type(credentials.password, delay=50)
                    password_filled = True
                    logger.debug(f"Filled password using selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Failed to fill password with selector {selector}: {e}")
        
        if not password_filled:
            logger.error("Could not find password field")
            return False
        
        # Submit the form
        submit_selectors = [
            'input[type="submit"]',
            'button[type="submit"]',
            'button:has-text("login")',
            'button:has-text("sign in")',
            'button:has-text("log in")',
            'button:has-text("Login")',
            'button:has-text("Sign In")',
            'button:has-text("Log In")',
            '.login-button',
            '.submit-button',
            '.btn-login',
            '.btn-signin',
            '[data-testid*="login"]',
            '[data-testid*="submit"]',
            'button[class*="login"]',
            'button[class*="submit"]'
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                # Wait for the submit button to be available and enabled
                await page.wait_for_selector(selector, timeout=3000)
                submit_button = await page.query_selector(selector)
                if submit_button:
                    # Check if button is enabled
                    is_disabled = await submit_button.get_attribute('disabled')
                    if is_disabled:
                        logger.debug(f"Submit button is disabled, waiting...")
                        await asyncio.sleep(1)
                        continue
                    
                    # Click the submit button
                    await submit_button.click()
                    submitted = True
                    logger.debug(f"Clicked submit using selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Failed to click submit with selector {selector}: {e}")
        
        if not submitted:
            # Try pressing Enter on password field as fallback
            try:
                password_input = await page.query_selector('input[type="password"]')
                if password_input:
                    await password_input.press('Enter')
                    submitted = True
                    logger.debug("Submitted form by pressing Enter on password field")
            except Exception as e:
                logger.debug(f"Failed to submit by pressing Enter: {e}")
        
        if not submitted:
            logger.error("Could not submit login form")
            return False
        
        # Wait for navigation/response after login
        try:
            # Wait for any navigation to complete
            await page.wait_for_load_state('domcontentloaded', timeout=15000)
            await asyncio.sleep(3)  # Give JavaScript time to process
            
            # Try to wait for network to be idle, but don't fail if it times out
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                logger.debug("Network didn't become idle, but continuing...")
                
        except Exception as e:
            logger.debug(f"Timeout waiting for page load after login: {e}")
        
        # Check if authentication was successful
        current_url = page.url
        page_content = await page.content()
        
        success = self._check_auth_success_dynamic(current_url, page_content, credentials.success_indicators)
        
        if success:
            self.authenticated = True
            # Get cookies from the browser
            cookies = await page.context.cookies()
            self.auth_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
            logger.info("Dynamic form authentication successful")
        else:
            logger.error("Dynamic form authentication failed")
        
        return success
    
    def _find_login_url(self, base_url: str) -> Optional[str]:
        """Try to find the login URL automatically."""
        parsed_url = urlparse(base_url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Common login URL patterns
        login_paths = [
            '/login',
            '/signin',
            '/sign-in',
            '/auth/login',
            '/user/login',
            '/account/login',
            '/admin/login',
            '/wp-login.php',  # WordPress
            '/admin',
            '/auth'
        ]
        
        for path in login_paths:
            login_url = urljoin(base_domain, path)
            try:
                response = requests.head(login_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Found potential login URL: {login_url}")
                    return login_url
            except Exception as e:
                logger.debug(f"Failed to check login URL {login_url}: {e}")
        
        logger.warning("Could not automatically find login URL")
        return None
    
    def _check_auth_success(self, response: requests.Response, success_indicators: List[str]) -> bool:
        """Check if authentication was successful based on response."""
        # Check for redirects to dashboard/profile pages
        if response.history:
            final_url = response.url.lower()
            for indicator in success_indicators:
                if indicator in final_url:
                    return True
        
        # Check response content for success indicators
        content = response.text.lower()
        for indicator in success_indicators:
            if indicator in content:
                return True
        
        # Check for common failure indicators
        failure_indicators = [
            "invalid", "incorrect", "failed", "error", "wrong",
            "login failed", "authentication failed", "access denied"
        ]
        
        for indicator in failure_indicators:
            if indicator in content:
                return False
        
        # If no clear indicators, assume success if status is 200 and we have cookies
        return response.status_code == 200 and len(response.cookies) > 0
    
    def _check_auth_success_dynamic(self, current_url: str, page_content: str, success_indicators: List[str]) -> bool:
        """Check if dynamic authentication was successful."""
        url_lower = current_url.lower()
        content_lower = page_content.lower()
        
        # Check URL for success indicators
        for indicator in success_indicators:
            if indicator in url_lower:
                return True
        
        # Check page content for success indicators
        for indicator in success_indicators:
            if indicator in content_lower:
                return True
        
        # Check for common failure indicators
        failure_indicators = [
            "invalid", "incorrect", "failed", "error", "wrong",
            "login failed", "authentication failed", "access denied"
        ]
        
        for indicator in failure_indicators:
            if indicator in content_lower:
                return False
        
        # Check if we're no longer on a login page
        login_indicators = ["login", "signin", "sign-in", "password", "username"]
        on_login_page = any(indicator in url_lower for indicator in login_indicators)
        
        return not on_login_page
    
    def apply_auth_to_session(self, session: requests.Session):
        """Apply authentication cookies/headers to a requests session."""
        if self.auth_cookies:
            session.cookies.update(self.auth_cookies)
        if self.auth_headers:
            session.headers.update(self.auth_headers)
    
    async def apply_auth_to_page(self, page: Page):
        """Apply authentication cookies to a Playwright page."""
        if self.auth_cookies:
            # Convert cookies to Playwright format
            playwright_cookies = []
            for name, value in self.auth_cookies.items():
                playwright_cookies.append({
                    'name': name,
                    'value': value,
                    'domain': urlparse(page.url).netloc,
                    'path': '/'
                })
            await page.context.add_cookies(playwright_cookies)


def create_auth_credentials(
    username: str,
    password: str,
    auth_type: str = "form",
    login_url: Optional[str] = None,
    **kwargs
) -> AuthCredentials:
    """Helper function to create authentication credentials."""
    return AuthCredentials(
        username=username,
        password=password,
        auth_type=auth_type,
        login_url=login_url,
        **kwargs
    ) 