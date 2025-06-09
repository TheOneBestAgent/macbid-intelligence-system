"""Web scraper module for fetching and analyzing web content."""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from abc import ABC, abstractmethod

import requests
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page
from urllib.robotparser import RobotFileParser

from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Container for scraped web content."""
    url: str
    html: str
    status_code: int
    headers: Dict[str, str]
    javascript_content: List[str]
    network_requests: List[Dict[str, Any]]
    cookies: Dict[str, str]
    response_time: float
    final_url: str  # After redirects
    error: Optional[str] = None


class BaseScraper(ABC):
    """Abstract base class for web scrapers."""
    
    def __init__(self):
        self.session = None
        self.rate_limiter = RateLimiter(config.get('scraping.rate_limit', 1.0))
    
    @abstractmethod
    async def scrape(self, url: str) -> ScrapedContent:
        """Scrape content from a URL."""
        pass
    
    def _should_respect_robots_txt(self, url: str) -> bool:
        """Check if we should respect robots.txt for this URL."""
        if not config.get('scraping.respect_robots_txt', True):
            return True
        
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            user_agent = config.get('scraping.user_agent', 'API-Endpoint-Scraper/1.0')
            return rp.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True  # Allow scraping if robots.txt check fails


class StaticScraper(BaseScraper):
    """Scraper for static content using requests."""
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self._configure_session()
    
    def _configure_session(self):
        """Configure the requests session."""
        self.session.headers.update({
            'User-Agent': config.get('scraping.user_agent', 'API-Endpoint-Scraper/1.0')
        })
        
        # Configure proxy if enabled
        if config.get('security.proxy.enabled', False):
            proxies = {
                'http': config.get('security.proxy.http', ''),
                'https': config.get('security.proxy.https', '')
            }
            self.session.proxies.update(proxies)
        
        # Configure SSL verification
        self.session.verify = config.get('security.verify_ssl', True)
    
    async def scrape(self, url: str) -> ScrapedContent:
        """Scrape static content from a URL."""
        if not self._should_respect_robots_txt(url):
            return ScrapedContent(
                url=url, html='', status_code=403, headers={},
                javascript_content=[], network_requests=[], cookies={},
                response_time=0, final_url=url,
                error="Blocked by robots.txt"
            )
        
        await self.rate_limiter.wait()
        
        start_time = time.time()
        try:
            response = self.session.get(
                url,
                timeout=config.get('scraping.timeout', 30),
                allow_redirects=config.get('security.allow_redirects', True)
            )
            response_time = time.time() - start_time
            
            # Extract JavaScript content from script tags
            soup = BeautifulSoup(response.text, 'html.parser')
            javascript_content = []
            for script in soup.find_all('script'):
                if script.string:
                    javascript_content.append(script.string)
                elif script.get('src'):
                    # Note: We could fetch external scripts here
                    javascript_content.append(f"// External script: {script.get('src')}")
            
            return ScrapedContent(
                url=url,
                html=response.text,
                status_code=response.status_code,
                headers=dict(response.headers),
                javascript_content=javascript_content,
                network_requests=[],  # Static scraper doesn't monitor network
                cookies=dict(response.cookies),
                response_time=response_time,
                final_url=response.url
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return ScrapedContent(
                url=url, html='', status_code=0, headers={},
                javascript_content=[], network_requests=[], cookies={},
                response_time=time.time() - start_time, final_url=url,
                error=str(e)
            )


class DynamicScraper(BaseScraper):
    """Scraper for dynamic content using Playwright."""
    
    def __init__(self):
        super().__init__()
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()
    
    async def _initialize_browser(self):
        """Initialize the Playwright browser."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            
            browser_type = config.get('scraping.browser.browser_type', 'chromium')
            browser_args = {
                'headless': config.get('scraping.browser.headless', True)
            }
            
            if browser_type == 'chromium':
                self.browser = await self.playwright.chromium.launch(**browser_args)
            elif browser_type == 'firefox':
                self.browser = await self.playwright.firefox.launch(**browser_args)
            elif browser_type == 'webkit':
                self.browser = await self.playwright.webkit.launch(**browser_args)
            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")
    
    async def _cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape(self, url: str, auth_credentials=None) -> ScrapedContent:
        """Scrape dynamic content from a URL."""
        if not self._should_respect_robots_txt(url):
            return ScrapedContent(
                url=url, html='', status_code=403, headers={},
                javascript_content=[], network_requests=[], cookies={},
                response_time=0, final_url=url,
                error="Blocked by robots.txt"
            )
        
        if not self.browser:
            await self._initialize_browser()
        
        await self.rate_limiter.wait()
        
        start_time = time.time()
        network_requests = []
        
        try:
            # Create a new page
            page = await self.browser.new_page()
            
            # Set viewport
            viewport = config.get('scraping.browser.viewport', {'width': 1920, 'height': 1080})
            await page.set_viewport_size(viewport)
            
            # Handle authentication if provided
            if auth_credentials:
                from .auth_handler import AuthHandler
                auth_handler = AuthHandler()
                auth_success = await auth_handler.authenticate_dynamic(auth_credentials, page, url)
                if not auth_success:
                    logger.warning("Authentication failed, proceeding without login")
                else:
                    logger.info("Authentication successful")
            
            # Monitor network requests
            async def handle_request(request):
                network_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data,
                    'resource_type': request.resource_type
                })
            
            page.on('request', handle_request)
            
            # Navigate to the page with more resilient strategy
            try:
                response = await page.goto(
                    url,
                    timeout=config.get('scraping.timeout', 30) * 1000,
                    wait_until='domcontentloaded'
                )
                
                # Try to wait for network idle, but don't fail if it times out
                try:
                    await page.wait_for_load_state('networkidle', timeout=30000)
                except Exception:
                    logger.debug("Network didn't become idle, but continuing with scraping...")
                    
            except Exception as e:
                logger.error(f"Failed to navigate to {url}: {e}")
                raise
            
            # Wait for additional content to load
            wait_time = config.get('scraping.browser.wait_for_load', 3.0)
            await asyncio.sleep(wait_time)
            
            # Get page content
            html = await page.content()
            
            # Extract JavaScript content
            javascript_content = []
            scripts = await page.query_selector_all('script')
            for script in scripts:
                content = await script.inner_text()
                if content.strip():
                    javascript_content.append(content)
                else:
                    src = await script.get_attribute('src')
                    if src:
                        javascript_content.append(f"// External script: {src}")
            
            # Get cookies
            cookies = await page.context.cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            response_time = time.time() - start_time
            
            await page.close()
            
            return ScrapedContent(
                url=url,
                html=html,
                status_code=response.status if response else 200,
                headers=dict(response.headers) if response else {},
                javascript_content=javascript_content,
                network_requests=network_requests,
                cookies=cookie_dict,
                response_time=response_time,
                final_url=page.url
            )
            
        except Exception as e:
            logger.error(f"Error scraping {url} with dynamic scraper: {e}")
            return ScrapedContent(
                url=url, html='', status_code=0, headers={},
                javascript_content=[], network_requests=[], cookies={},
                response_time=time.time() - start_time, final_url=url,
                error=str(e)
            )


class RateLimiter:
    """Rate limiter to respect scraping limits."""
    
    def __init__(self, delay: float):
        self.delay = delay
        self.last_request = 0
    
    async def wait(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()
        time_since_last = now - self.last_request
        
        if time_since_last < self.delay:
            wait_time = self.delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request = time.time()


class ScraperFactory:
    """Factory for creating appropriate scrapers."""
    
    @staticmethod
    def create_scraper(scraper_type: str = 'auto') -> BaseScraper:
        """Create a scraper instance.
        
        Args:
            scraper_type: Type of scraper ('static', 'dynamic', 'auto')
            
        Returns:
            Scraper instance
        """
        if scraper_type == 'static':
            return StaticScraper()
        elif scraper_type == 'dynamic':
            return DynamicScraper()
        elif scraper_type == 'auto':
            # For now, default to static. Could add logic to detect SPA/dynamic content
            return StaticScraper()
        else:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
    
    @staticmethod
    async def create_dynamic_scraper() -> DynamicScraper:
        """Create and initialize a dynamic scraper."""
        scraper = DynamicScraper()
        await scraper._initialize_browser()
        return scraper


class WebScraper:
    """Main web scraper orchestrator."""
    
    def __init__(self):
        self.static_scraper = StaticScraper()
        self.dynamic_scraper = None
    
    async def scrape_url(self, url: str, use_dynamic: bool = False, auth_credentials=None) -> ScrapedContent:
        """Scrape a single URL.
        
        Args:
            url: URL to scrape
            use_dynamic: Whether to use dynamic scraping (Playwright)
            auth_credentials: Authentication credentials for login
            
        Returns:
            Scraped content
        """
        if use_dynamic:
            if not self.dynamic_scraper:
                self.dynamic_scraper = await ScraperFactory.create_dynamic_scraper()
            return await self.dynamic_scraper.scrape(url, auth_credentials)
        else:
            return await self.static_scraper.scrape(url)
    
    async def scrape_urls(self, urls: List[str], use_dynamic: bool = False) -> List[ScrapedContent]:
        """Scrape multiple URLs.
        
        Args:
            urls: List of URLs to scrape
            use_dynamic: Whether to use dynamic scraping
            
        Returns:
            List of scraped content
        """
        if config.get('performance.parallel_processing', True):
            # Parallel processing with concurrency limit
            semaphore = asyncio.Semaphore(config.get('scraping.max_concurrent', 10))
            
            async def scrape_with_semaphore(url):
                async with semaphore:
                    return await self.scrape_url(url, use_dynamic)
            
            tasks = [scrape_with_semaphore(url) for url in urls]
            return await asyncio.gather(*tasks)
        else:
            # Sequential processing
            results = []
            for url in urls:
                result = await self.scrape_url(url, use_dynamic)
                results.append(result)
            return results
    
    async def cleanup(self):
        """Clean up resources."""
        if self.dynamic_scraper:
            await self.dynamic_scraper._cleanup() 