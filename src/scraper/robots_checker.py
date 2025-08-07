"""Check robots.txt compliance for web scraping."""

import time
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from typing import Optional, Dict, Any
from loguru import logger


class RobotsChecker:
    """Handle robots.txt checking for respectful web scraping."""
    
    def __init__(self, base_url: str, user_agent: str):
        """Initialize robots checker.
        
        Args:
            base_url: The base URL of the website
            user_agent: The user agent string to check against
        """
        self.base_url = base_url
        self.user_agent = user_agent
        self.robot_parser = RobotFileParser()
        self._robots_cache: Dict[str, Any] = {}
        self._load_robots_txt()
        
    def _load_robots_txt(self) -> None:
        """Load and parse robots.txt from the website."""
        parsed_url = urlparse(self.base_url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        logger.info(f"Checking robots.txt at {robots_url}")
        
        try:
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
            self._robots_cache['loaded'] = True
            self._robots_cache['load_time'] = time.time()
            
            # Get crawl delay if specified
            crawl_delay = self.robot_parser.crawl_delay(self.user_agent)
            if crawl_delay is not None:
                self._robots_cache['crawl_delay'] = crawl_delay
                logger.info(f"Robots.txt specifies crawl delay: {crawl_delay}s")
            else:
                self._robots_cache['crawl_delay'] = None
                
        except Exception as e:
            logger.warning(f"Could not fetch robots.txt: {e}")
            logger.info("Proceeding with caution - will use conservative rate limiting")
            self._robots_cache['loaded'] = False
            self._robots_cache['crawl_delay'] = 1.0  # Default conservative delay
            
    def can_fetch(self, url: str) -> bool:
        """Check if the given URL can be fetched according to robots.txt.
        
        Args:
            url: The URL to check
            
        Returns:
            True if the URL can be fetched, False otherwise
        """
        if not self._robots_cache.get('loaded', False):
            # If robots.txt couldn't be loaded, be conservative
            logger.debug(f"No robots.txt loaded, allowing fetch of {url}")
            return True
            
        can_fetch = self.robot_parser.can_fetch(self.user_agent, url)
        
        if not can_fetch:
            logger.warning(f"Robots.txt disallows fetching: {url}")
        else:
            logger.debug(f"Robots.txt allows fetching: {url}")
            
        return can_fetch
        
    def get_crawl_delay(self) -> Optional[float]:
        """Get the crawl delay specified in robots.txt.
        
        Returns:
            The crawl delay in seconds, or None if not specified
        """
        return self._robots_cache.get('crawl_delay')
        
    def get_request_rate(self) -> Optional[tuple]:
        """Get the request rate from robots.txt if specified.
        
        Returns:
            A tuple of (requests, seconds) or None if not specified
        """
        if not self._robots_cache.get('loaded', False):
            return None
            
        request_rate = self.robot_parser.request_rate(self.user_agent)
        if request_rate:
            return (request_rate.requests, request_rate.seconds)
        return None
        
    def check_compliance(self, urls: list) -> Dict[str, Any]:
        """Check compliance for a list of URLs.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            A dictionary with compliance information
        """
        allowed_urls = []
        disallowed_urls = []
        
        for url in urls:
            if self.can_fetch(url):
                allowed_urls.append(url)
            else:
                disallowed_urls.append(url)
                
        return {
            'total_urls': len(urls),
            'allowed': len(allowed_urls),
            'disallowed': len(disallowed_urls),
            'crawl_delay': self.get_crawl_delay(),
            'request_rate': self.get_request_rate(),
            'allowed_urls': allowed_urls,
            'disallowed_urls': disallowed_urls
        }