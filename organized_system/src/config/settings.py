"""Configuration management for the API endpoint scraper."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the scraper."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self._apply_env_overrides()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Check environment variable first
        env_path = os.getenv('SCRAPER_CONFIG_PATH')
        if env_path and os.path.exists(env_path):
            return env_path
        
        # Look for config in standard locations
        possible_paths = [
            'config/default.yaml',
            'config.yaml',
            os.path.expanduser('~/.api-scraper/config.yaml'),
            '/etc/api-scraper/config.yaml'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return default path (will be created if needed)
        return 'config/default.yaml'
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config or {}
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'scraping': {
                'timeout': 30,
                'rate_limit': 1.0,
                'user_agent': 'API-Endpoint-Scraper/1.0',
                'respect_robots_txt': True,
                'max_concurrent': 10,
                'retry_attempts': 3,
                'retry_delay': 2.0,
                'browser': {
                    'headless': True,
                    'browser_type': 'chromium',
                    'viewport': {'width': 1920, 'height': 1080},
                    'wait_for_load': 3.0
                }
            },
            'extraction': {
                'patterns': {
                    'rest_api': ['api/v\\d+/', '/api/', 'rest/', '/v\\d+/', 'service/', 'endpoint/'],
                    'graphql': ['graphql', 'graph', 'gql'],
                    'websocket': ['ws://', 'wss://', 'socket.io', 'websocket']
                },
                'javascript_analysis': True,
                'network_monitoring': True,
                'source_map_analysis': False,
                'documentation_parsing': True,
                'confidence_weights': {
                    'network_request': 0.9,
                    'javascript_call': 0.8,
                    'html_form': 0.7,
                    'documentation': 0.9,
                    'pattern_match': 0.6
                }
            },
            'output': {
                'format': 'json',
                'file': 'endpoints.json',
                'include_metadata': True,
                'pretty_print': True,
                'include_sections': {
                    'summary': True,
                    'endpoints': True,
                    'statistics': True,
                    'raw_data': False
                },
                'min_confidence': 0.5,
                'exclude_static_assets': True,
                'deduplicate': True
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'scraper.log',
                'console_output': True
            },
            'security': {
                'verify_ssl': True,
                'allow_redirects': True,
                'max_redirects': 5,
                'proxy': {'enabled': False, 'http': '', 'https': ''},
                'auth': {'enabled': False, 'type': 'basic', 'credentials': {}}
            },
            'performance': {
                'memory_limit_mb': 500,
                'cache_enabled': True,
                'cache_size_mb': 100,
                'parallel_processing': True
            }
        }
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        # Log level override
        log_level = os.getenv('SCRAPER_LOG_LEVEL')
        if log_level:
            self.config['logging']['level'] = log_level.upper()
        
        # Output directory override
        output_dir = os.getenv('SCRAPER_OUTPUT_DIR')
        if output_dir:
            filename = self.config['output']['file']
            self.config['output']['file'] = os.path.join(output_dir, filename)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'scraping.timeout')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'scraping.timeout')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save(self, path: Optional[str] = None):
        """Save configuration to file.
        
        Args:
            path: Path to save to. If None, uses current config path.
        """
        save_path = path or self.config_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {save_path}")


# Global configuration instance
config = Config() 