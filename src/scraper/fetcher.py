import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from ..utils.config import config
from ..utils.file_utils import ensure_directory, sanitize_filename


class DigimonScraper:
    """Scraper for digimon.net/reference website."""
    
    def __init__(self):
        """Initialize scraper with configuration."""
        self.base_url = config.get("scraping.base_url")
        self.delay = config.get("scraping.delay", 1.0)
        self.timeout = config.get("scraping.timeout", 30)
        self.max_retries = config.get("scraping.max_retries", 3)
        self.user_agent = config.get("scraping.user_agent")
        self.concurrent_requests = config.get("scraping.concurrent_requests", 3)
        
        # Paths
        self.html_dir = Path(config.get("paths.raw_html"))
        self.images_dir = Path(config.get("paths.raw_images"))
        ensure_directory(self.html_dir)
        ensure_directory(self.images_dir)
        
        # Session headers
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        # Track progress
        self.scraped_urls: List[str] = []
        self.failed_urls: List[Tuple[str, str]] = []
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a single page with retry logic."""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
            
    async def fetch_page_async(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Tuple[str, Optional[str]]:
        """Fetch a page asynchronously."""
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.text()
                return url, content
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return url, None
            
    def get_digimon_urls(self) -> List[str]:
        """Extract all Digimon detail page URLs from the index."""
        logger.info("Fetching Digimon index page...")
        
        try:
            html = self.fetch_page(self.base_url)
            if not html:
                raise ValueError("Failed to fetch index page")
                
            soup = BeautifulSoup(html, 'lxml')
            
            # Find all Digimon links
            # This selector might need adjustment based on actual HTML structure
            digimon_links = []
            
            # Try multiple possible selectors
            selectors = [
                'a[href*="/detail/"]',
                'a.digimon-link',
                '.digimon-list a',
                'a[href*="digimon"]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    logger.info(f"Found {len(links)} links with selector: {selector}")
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            digimon_links.append(full_url)
                    break
                    
            # Deduplicate
            digimon_links = list(set(digimon_links))
            logger.info(f"Found {len(digimon_links)} unique Digimon URLs")
            
            return digimon_links
            
        except Exception as e:
            logger.error(f"Error getting Digimon URLs: {e}")
            return []
            
    def save_html(self, url: str, html: str) -> Path:
        """Save HTML content to file."""
        # Extract ID from URL
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # Use last part of URL as ID, or generate from full path
        if path_parts and path_parts[-1]:
            digimon_id = sanitize_filename(path_parts[-1])
        else:
            digimon_id = sanitize_filename('_'.join(path_parts))
            
        file_path = self.html_dir / f"{digimon_id}.html"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
            
        logger.debug(f"Saved HTML: {file_path}")
        return file_path
        
    def download_image(self, image_url: str, digimon_name: str) -> Optional[Path]:
        """Download and save Digimon image."""
        try:
            response = requests.get(
                image_url,
                headers=self.headers,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            else:
                # Try to get from URL
                ext = Path(urlparse(image_url).path).suffix or '.jpg'
                
            filename = sanitize_filename(digimon_name) + ext
            file_path = self.images_dir / filename
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.debug(f"Downloaded image: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading image {image_url}: {e}")
            return None
            
    def scrape_all(self) -> Dict[str, any]:
        """Scrape all Digimon pages synchronously."""
        urls = self.get_digimon_urls()
        
        if not urls:
            logger.error("No URLs found to scrape")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "failed_urls": []
            }
            
        logger.info(f"Starting to scrape {len(urls)} Digimon pages...")
        
        # Progress bar
        with tqdm(total=len(urls), desc="Scraping") as pbar:
            for url in urls:
                try:
                    # Respect rate limit
                    time.sleep(self.delay)
                    
                    # Fetch page
                    html = self.fetch_page(url)
                    if html:
                        self.save_html(url, html)
                        self.scraped_urls.append(url)
                        
                        # Extract and download image
                        soup = BeautifulSoup(html, 'lxml')
                        img_tag = soup.select_one('img.digimon-image, img[alt*="digimon"]')
                        if img_tag and img_tag.get('src'):
                            img_url = urljoin(url, img_tag['src'])
                            name = soup.select_one('.c-titleSet__main')
                            if name:
                                self.download_image(img_url, name.text.strip())
                                
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
                    self.failed_urls.append((url, str(e)))
                    
                pbar.update(1)
                
        # Summary
        summary = {
            "total": len(urls),
            "success": len(self.scraped_urls),
            "failed": len(self.failed_urls),
            "failed_urls": self.failed_urls
        }
        
        logger.info(f"Scraping complete: {summary['success']}/{summary['total']} successful")
        
        # Save summary
        import json
        with open(self.html_dir.parent / "scrape_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
            
        return summary
        
    async def scrape_all_async(self) -> Dict[str, any]:
        """Scrape all Digimon pages asynchronously for better performance."""
        urls = self.get_digimon_urls()
        
        if not urls:
            logger.error("No URLs found to scrape")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "failed_urls": []
            }
            
        logger.info(f"Starting async scrape of {len(urls)} Digimon pages...")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.concurrent_requests)
        
        async def fetch_with_delay(session, url):
            async with semaphore:
                result = await self.fetch_page_async(session, url)
                await asyncio.sleep(self.delay)
                return result
                
        # Create session and fetch all pages
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [fetch_with_delay(session, url) for url in urls]
            
            # Process with progress bar
            results = []
            with tqdm(total=len(tasks), desc="Fetching pages") as pbar:
                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    results.append(result)
                    pbar.update(1)
                    
        # Process results
        for url, html in results:
            if html:
                self.save_html(url, html)
                self.scraped_urls.append(url)
            else:
                self.failed_urls.append((url, "Failed to fetch"))
                
        # Summary
        summary = {
            "total": len(urls),
            "success": len(self.scraped_urls),
            "failed": len(self.failed_urls),
            "failed_urls": self.failed_urls
        }
        
        logger.info(f"Async scraping complete: {summary['success']}/{summary['total']} successful")
        
        return summary