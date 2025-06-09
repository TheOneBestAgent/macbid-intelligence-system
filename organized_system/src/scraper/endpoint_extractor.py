"""Endpoint extraction engine for discovering API endpoints from scraped content."""

import re
import json
import logging
from typing import List, Dict, Set, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from dataclasses import dataclass
from datetime import datetime
import ast

from .web_scraper import ScrapedContent
from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class Endpoint:
    """Represents a discovered API endpoint."""
    url: str
    method: str
    endpoint_type: str  # rest, graphql, websocket, other
    parameters: List[str]
    headers: Dict[str, str]
    source: str  # javascript, html, network, documentation
    confidence: float  # 0.0 to 1.0
    discovered_at: str
    metadata: Dict[str, Any]


class EndpointExtractor:
    """Main class for extracting API endpoints from scraped content."""
    
    def __init__(self):
        self.patterns = self._load_patterns()
        self.confidence_weights = config.get('extraction.confidence_weights', {})
        self.min_confidence = config.get('output.min_confidence', 0.5)
    
    def _load_patterns(self) -> Dict[str, List[str]]:
        """Load endpoint patterns from configuration."""
        return config.get('extraction.patterns', {
            'rest_api': [r'api/v\d+/', r'/api/', r'rest/', r'/v\d+/', r'service/', r'endpoint/'],
            'graphql': [r'graphql', r'graph', r'gql'],
            'websocket': [r'ws://', r'wss://', r'socket\.io', r'websocket']
        })
    
    def extract_endpoints(self, content: ScrapedContent) -> List[Endpoint]:
        """Extract all endpoints from scraped content.
        
        Args:
            content: Scraped web content
            
        Returns:
            List of discovered endpoints
        """
        endpoints = []
        
        # Extract from different sources
        if config.get('extraction.javascript_analysis', True):
            endpoints.extend(self._extract_from_javascript(content))
        
        endpoints.extend(self._extract_from_html(content))
        
        if config.get('extraction.network_monitoring', True):
            endpoints.extend(self._extract_from_network_requests(content))
        
        if config.get('extraction.documentation_parsing', True):
            endpoints.extend(self._extract_from_documentation(content))
        
        # Deduplicate and filter by confidence
        endpoints = self._deduplicate_endpoints(endpoints)
        endpoints = [ep for ep in endpoints if ep.confidence >= self.min_confidence]
        
        return endpoints
    
    def _extract_from_javascript(self, content: ScrapedContent) -> List[Endpoint]:
        """Extract endpoints from JavaScript code."""
        endpoints = []
        
        for js_content in content.javascript_content:
            if js_content.startswith('// External script:'):
                # Handle external script references
                script_url = js_content.replace('// External script: ', '')
                endpoints.extend(self._analyze_script_url(script_url, content.url))
            else:
                # Analyze inline JavaScript
                endpoints.extend(self._analyze_javascript_code(js_content, content.url))
        
        return endpoints
    
    def _analyze_javascript_code(self, js_code: str, base_url: str) -> List[Endpoint]:
        """Analyze JavaScript code for API calls."""
        endpoints = []
        
        # Common patterns for API calls
        api_patterns = [
            # fetch() calls
            r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'fetch\s*\(\s*([^,\)]+)',
            
            # XMLHttpRequest
            r'\.open\s*\(\s*[\'"`](\w+)[\'"`]\s*,\s*[\'"`]([^\'"`]+)[\'"`]',
            
            # jQuery AJAX
            r'\$\.ajax\s*\(\s*\{[^}]*url\s*:\s*[\'"`]([^\'"`]+)[\'"`]',
            r'\$\.get\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'\$\.post\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            
            # Axios
            r'axios\.\w+\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'axios\s*\(\s*\{[^}]*url\s*:\s*[\'"`]([^\'"`]+)[\'"`]',
            
            # General URL patterns
            r'[\'"`](/api/[^\'"`]+)[\'"`]',
            r'[\'"`](https?://[^\'"`]+/api/[^\'"`]+)[\'"`]',
        ]
        
        for pattern in api_patterns:
            matches = re.finditer(pattern, js_code, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:  # Method and URL
                    method, url = match.groups()
                    method = method.upper()
                else:  # Just URL
                    url = match.group(1)
                    method = 'GET'  # Default method
                
                # Clean and validate URL
                url = self._clean_url(url, base_url)
                if url and self._is_api_endpoint(url):
                    endpoint = Endpoint(
                        url=url,
                        method=method,
                        endpoint_type=self._classify_endpoint(url),
                        parameters=self._extract_parameters_from_url(url),
                        headers={},
                        source='javascript',
                        confidence=self.confidence_weights.get('javascript_call', 0.8),
                        discovered_at=datetime.now().isoformat(),
                        metadata={'pattern': pattern, 'raw_match': match.group(0)}
                    )
                    endpoints.append(endpoint)
        
        # Look for GraphQL queries
        graphql_patterns = [
            r'query\s+\w+\s*\{[^}]+\}',
            r'mutation\s+\w+\s*\{[^}]+\}',
            r'subscription\s+\w+\s*\{[^}]+\}'
        ]
        
        for pattern in graphql_patterns:
            matches = re.finditer(pattern, js_code, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Try to find the GraphQL endpoint URL
                graphql_url = self._find_graphql_endpoint(js_code, base_url)
                if graphql_url:
                    endpoint = Endpoint(
                        url=graphql_url,
                        method='POST',
                        endpoint_type='graphql',
                        parameters=[],
                        headers={'Content-Type': 'application/json'},
                        source='javascript',
                        confidence=self.confidence_weights.get('javascript_call', 0.8),
                        discovered_at=datetime.now().isoformat(),
                        metadata={'query': match.group(0)[:200]}  # First 200 chars
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_from_html(self, content: ScrapedContent) -> List[Endpoint]:
        """Extract endpoints from HTML content."""
        endpoints = []
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content.html, 'html.parser')
        
        # Extract from forms
        forms = soup.find_all('form')
        for form in forms:
            action = form.get('action', '')
            method = form.get('method', 'GET').upper()
            
            if action:
                url = self._clean_url(action, content.url)
                if url and self._is_api_endpoint(url):
                    # Extract form parameters
                    parameters = []
                    inputs = form.find_all(['input', 'select', 'textarea'])
                    for inp in inputs:
                        name = inp.get('name')
                        if name:
                            parameters.append(name)
                    
                    endpoint = Endpoint(
                        url=url,
                        method=method,
                        endpoint_type=self._classify_endpoint(url),
                        parameters=parameters,
                        headers={},
                        source='html',
                        confidence=self.confidence_weights.get('html_form', 0.7),
                        discovered_at=datetime.now().isoformat(),
                        metadata={'form_id': form.get('id', ''), 'form_class': form.get('class', [])}
                    )
                    endpoints.append(endpoint)
        
        # Extract from links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            url = self._clean_url(href, content.url)
            if url and self._is_api_endpoint(url):
                endpoint = Endpoint(
                    url=url,
                    method='GET',
                    endpoint_type=self._classify_endpoint(url),
                    parameters=self._extract_parameters_from_url(url),
                    headers={},
                    source='html',
                    confidence=self.confidence_weights.get('pattern_match', 0.6),
                    discovered_at=datetime.now().isoformat(),
                    metadata={'link_text': link.get_text()[:100]}
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_from_network_requests(self, content: ScrapedContent) -> List[Endpoint]:
        """Extract endpoints from monitored network requests."""
        endpoints = []
        
        for request in content.network_requests:
            url = request.get('url', '')
            method = request.get('method', 'GET').upper()
            
            if self._is_api_endpoint(url):
                # Extract parameters from POST data
                parameters = []
                post_data = request.get('post_data')
                if post_data:
                    try:
                        # Try to parse as JSON
                        json_data = json.loads(post_data)
                        if isinstance(json_data, dict):
                            parameters = list(json_data.keys())
                    except json.JSONDecodeError:
                        # Try to parse as form data
                        if '=' in post_data:
                            parameters = [param.split('=')[0] for param in post_data.split('&')]
                
                endpoint = Endpoint(
                    url=url,
                    method=method,
                    endpoint_type=self._classify_endpoint(url),
                    parameters=parameters,
                    headers=request.get('headers', {}),
                    source='network',
                    confidence=self.confidence_weights.get('network_request', 0.9),
                    discovered_at=datetime.now().isoformat(),
                    metadata={
                        'resource_type': request.get('resource_type', ''),
                        'post_data_size': len(post_data) if post_data else 0
                    }
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_from_documentation(self, content: ScrapedContent) -> List[Endpoint]:
        """Extract endpoints from API documentation."""
        endpoints = []
        
        # Look for OpenAPI/Swagger documentation
        swagger_patterns = [
            r'"paths"\s*:\s*\{([^}]+)\}',
            r'swagger:\s*[\'"`]([^\'"`]+)[\'"`]',
            r'openapi:\s*[\'"`]([^\'"`]+)[\'"`]'
        ]
        
        for pattern in swagger_patterns:
            matches = re.finditer(pattern, content.html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # This is a simplified extraction - in practice, you'd want to parse the full OpenAPI spec
                paths_content = match.group(1) if match.groups() else match.group(0)
                
                # Extract path patterns
                path_matches = re.finditer(r'[\'"`](/[^\'"`]+)[\'"`]', paths_content)
                for path_match in path_matches:
                    path = path_match.group(1)
                    if self._is_api_endpoint(path):
                        full_url = urljoin(content.url, path)
                        endpoint = Endpoint(
                            url=full_url,
                            method='GET',  # Default, would need full parsing for actual methods
                            endpoint_type=self._classify_endpoint(path),
                            parameters=[],
                            headers={},
                            source='documentation',
                            confidence=self.confidence_weights.get('documentation', 0.9),
                            discovered_at=datetime.now().isoformat(),
                            metadata={'documentation_type': 'openapi'}
                        )
                        endpoints.append(endpoint)
        
        return endpoints
    
    def _clean_url(self, url: str, base_url: str) -> Optional[str]:
        """Clean and normalize URL."""
        if not url:
            return None
        
        # Remove quotes and whitespace
        url = url.strip('\'"` \t\n\r')
        
        # Skip data URLs, javascript, etc.
        if url.startswith(('data:', 'javascript:', 'mailto:', '#')):
            return None
        
        # Convert relative URLs to absolute
        if url.startswith('/'):
            parsed_base = urlparse(base_url)
            url = f"{parsed_base.scheme}://{parsed_base.netloc}{url}"
        elif not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        return url
    
    def _is_api_endpoint(self, url: str) -> bool:
        """Check if URL looks like an API endpoint."""
        if not url:
            return False
        
        # Check against configured patterns
        for endpoint_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return True
        
        # Additional heuristics
        api_indicators = [
            '/api/', '/rest/', '/service/', '/endpoint/',
            '.json', '.xml', '/v1/', '/v2/', '/v3/',
            'graphql', 'gql'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in api_indicators)
    
    def _classify_endpoint(self, url: str) -> str:
        """Classify the type of API endpoint."""
        url_lower = url.lower()
        
        # Check GraphQL
        if any(pattern in url_lower for pattern in ['graphql', 'gql', 'graph']):
            return 'graphql'
        
        # Check WebSocket
        if url.startswith(('ws://', 'wss://')) or 'websocket' in url_lower or 'socket.io' in url_lower:
            return 'websocket'
        
        # Check REST API patterns
        rest_patterns = ['/api/', '/rest/', '/service/', '/v1/', '/v2/', '/v3/']
        if any(pattern in url_lower for pattern in rest_patterns):
            return 'rest'
        
        return 'other'
    
    def _extract_parameters_from_url(self, url: str) -> List[str]:
        """Extract parameters from URL query string."""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        return list(query_params.keys())
    
    def _find_graphql_endpoint(self, js_code: str, base_url: str) -> Optional[str]:
        """Try to find GraphQL endpoint URL in JavaScript code."""
        # Look for common GraphQL endpoint patterns
        patterns = [
            r'[\'"`]([^\'"`]*graphql[^\'"`]*)[\'"`]',
            r'[\'"`]([^\'"`]*/gql[^\'"`]*)[\'"`]',
            r'[\'"`]([^\'"`]*/graph[^\'"`]*)[\'"`]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, js_code, re.IGNORECASE)
            if match:
                url = match.group(1)
                return self._clean_url(url, base_url)
        
        return None
    
    def _analyze_script_url(self, script_url: str, base_url: str) -> List[Endpoint]:
        """Analyze external script URL for potential endpoints."""
        endpoints = []
        
        # Clean the script URL
        clean_url = self._clean_url(script_url, base_url)
        if clean_url and self._is_api_endpoint(clean_url):
            endpoint = Endpoint(
                url=clean_url,
                method='GET',
                endpoint_type=self._classify_endpoint(clean_url),
                parameters=[],
                headers={},
                source='javascript',
                confidence=self.confidence_weights.get('pattern_match', 0.6),
                discovered_at=datetime.now().isoformat(),
                metadata={'source': 'external_script'}
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _deduplicate_endpoints(self, endpoints: List[Endpoint]) -> List[Endpoint]:
        """Remove duplicate endpoints, keeping the one with highest confidence."""
        if not config.get('output.deduplicate', True):
            return endpoints
        
        # Group by URL and method
        endpoint_groups = {}
        for endpoint in endpoints:
            key = (endpoint.url, endpoint.method)
            if key not in endpoint_groups:
                endpoint_groups[key] = []
            endpoint_groups[key].append(endpoint)
        
        # Keep the endpoint with highest confidence from each group
        deduplicated = []
        for group in endpoint_groups.values():
            best_endpoint = max(group, key=lambda ep: ep.confidence)
            
            # Merge metadata from all endpoints in the group
            all_sources = set(ep.source for ep in group)
            best_endpoint.metadata['all_sources'] = list(all_sources)
            
            deduplicated.append(best_endpoint)
        
        return deduplicated 