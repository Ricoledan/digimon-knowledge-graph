import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import aiohttp
import requests
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from ..utils.config import config
from ..utils.file_utils import ensure_directory, sanitize_filename
from .robots_checker import RobotsChecker


class DigimonScraper:
    """Scraper for digimon.net/reference website."""
    
    def __init__(self):
        """Initialize scraper with configuration."""
        self.base_url = config.get("scraping.base_url")
        self.index_url = "https://digimon.net/reference/index.php"
        self.delay = config.get("scraping.delay", 1.0)
        self.timeout = config.get("scraping.timeout", 30)
        self.max_retries = config.get("scraping.max_retries", 3)
        self.user_agent = config.get("scraping.user_agent")
        self.concurrent_requests = config.get("scraping.concurrent_requests", 3)
        self.respect_robots = config.get("scraping.respect_robots_txt", True)
        
        # Initialize robots.txt checker
        if self.respect_robots:
            self.robots_checker = RobotsChecker(self.base_url, self.user_agent)
            # Update delay based on robots.txt if specified
            robots_delay = self.robots_checker.get_crawl_delay()
            if robots_delay and robots_delay > self.delay:
                logger.info(f"Updating crawl delay from {self.delay}s to {robots_delay}s based on robots.txt")
                self.delay = robots_delay
        
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
            
    def get_digimon_urls(self, use_api_urls: bool = False) -> List[str]:
        """Extract all Digimon detail page URLs from the index.
        
        Args:
            use_api_urls: If True, use URLs from API fetch instead of scraping index
        """
        # Check if we should use API-generated URLs
        if use_api_urls:
            api_urls_file = self.html_dir / "_all_digimon_urls.json"
            if api_urls_file.exists():
                logger.info(f"Loading URLs from API fetch: {api_urls_file}")
                with open(api_urls_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    urls = data.get('urls', [])
                    logger.info(f"Loaded {len(urls)} URLs from API fetch")
                    return urls
            else:
                logger.warning(f"API URLs file not found: {api_urls_file}")
                logger.info("Falling back to index page scraping")
        
        logger.info(f"Fetching Digimon index page from {self.index_url}")
        
        # Check if we can fetch the index page according to robots.txt
        if self.respect_robots and not self.robots_checker.can_fetch(self.index_url):
            logger.error(f"Robots.txt disallows fetching the index page: {self.index_url}")
            return []
        
        try:
            html = self.fetch_page(self.index_url)
            if not html:
                raise ValueError("Failed to fetch index page")
                
            soup = BeautifulSoup(html, 'lxml')
            
            # Save index page for investigation
            index_path = self.html_dir / "_index.html"
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Saved index page to {index_path}")
            
            # Find all Digimon links
            # Based on the URL pattern, looking for links to detail pages
            digimon_links = []
            
            # Try multiple possible selectors
            selectors = [
                'a[href*="detail.php"]',  # Common pattern for detail pages
                'a[href*="/detail/"]',
                'a[href*="?id="]',        # Query parameter pattern
                '.digimon-list a',
                '.list a',
                'table a',                # Often in tables
                'a[href^="detail"]'       # Relative links starting with detail
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    logger.info(f"Found {len(links)} links with selector: {selector}")
                    for link in links:
                        href = link.get('href')
                        if href:
                            # Convert relative URLs to absolute
                            full_url = urljoin(self.index_url, href)
                            # Only add if it's actually a detail page
                            if 'detail' in full_url or 'id=' in full_url:
                                digimon_links.append(full_url)
                    if digimon_links:  # If we found links, stop trying other selectors
                        break
                        
            # If no specific selectors worked, try a broader approach
            if not digimon_links:
                logger.info("Trying broader link search...")
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href')
                    full_url = urljoin(self.index_url, href)
                    # Look for patterns that might indicate detail pages
                    if any(pattern in full_url for pattern in ['detail', 'digimon', 'id=', 'name=']):
                        # Exclude common non-detail pages
                        if not any(exclude in full_url for exclude in ['index', 'list', 'search', 'login', 'register']):
                            digimon_links.append(full_url)
                    
            # Deduplicate and sort
            digimon_links = sorted(list(set(digimon_links)))
            logger.info(f"Found {len(digimon_links)} unique Digimon URLs")
            
            # Check robots.txt compliance for all URLs
            if self.respect_robots and digimon_links:
                logger.info("Checking robots.txt compliance for all URLs...")
                compliance = self.robots_checker.check_compliance(digimon_links)
                logger.info(f"Robots.txt compliance: {compliance['allowed']} allowed, {compliance['disallowed']} disallowed")
                
                if compliance['disallowed'] > 0:
                    logger.warning(f"Removing {compliance['disallowed']} disallowed URLs")
                    digimon_links = compliance['allowed_urls']
            
            # Save URL list for reference
            urls_file = self.html_dir / "_urls.json"
            with open(urls_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'index_url': self.index_url,
                    'total_urls': len(digimon_links),
                    'urls': digimon_links
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved URL list to {urls_file}")
            
            return digimon_links
            
        except Exception as e:
            logger.error(f"Error getting Digimon URLs: {e}")
            return []
            
    def save_html(self, url: str, html: str) -> Path:
        """Save HTML content to file."""
        # Extract ID from URL
        parsed = urlparse(url)
        
        # Check for query parameters first (e.g., ?directory_name=nyabootmon)
        if parsed.query:
            # Parse query parameters
            params = parse_qs(parsed.query)
            
            # Look for common parameter names
            digimon_id = None
            for param_name in ['directory_name', 'name', 'id', 'digimon']:
                if param_name in params and params[param_name]:
                    digimon_id = sanitize_filename(params[param_name][0])
                    break
            
            # If no ID found in params, use the whole query string
            if not digimon_id:
                digimon_id = sanitize_filename(parsed.query)
        else:
            # Original logic for path-based URLs
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
            
    def scrape_all(self, use_api_urls: bool = False) -> Dict[str, any]:
        """Scrape all Digimon pages synchronously."""
        urls = self.get_digimon_urls(use_api_urls=use_api_urls)
        
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
                    # Check robots.txt compliance
                    if self.respect_robots and not self.robots_checker.can_fetch(url):
                        logger.warning(f"Skipping {url} - disallowed by robots.txt")
                        self.failed_urls.append((url, "Disallowed by robots.txt"))
                        continue
                    
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
        with open(self.html_dir.parent / "scrape_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
            
        return summary
        
    async def scrape_all_async(self, use_api_urls: bool = False) -> Dict[str, any]:
        """Scrape all Digimon pages asynchronously for better performance."""
        urls = self.get_digimon_urls(use_api_urls=use_api_urls)
        
        if not urls:
            logger.error("No URLs found to scrape")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "failed_urls": []
            }
            
        logger.info(f"Starting async scrape of {len(urls)} Digimon pages...")
        logger.info(f"Configuration: {self.concurrent_requests} concurrent requests, {self.delay}s delay")
        
        # Reset counters
        self.scraped_urls = []
        self.failed_urls = []
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.concurrent_requests)
        
        async def fetch_with_delay(session, url, pbar):
            async with semaphore:
                # Check robots.txt compliance
                if self.respect_robots and not self.robots_checker.can_fetch(url):
                    logger.warning(f"Skipping {url} - disallowed by robots.txt")
                    self.failed_urls.append((url, "Disallowed by robots.txt"))
                    pbar.update(1)
                    return url, None
                
                result = await self.fetch_page_async(session, url)
                await asyncio.sleep(self.delay)
                
                # Update progress with status
                url_str, content = result
                if content:
                    digimon_name = url_str.split('=')[-1][:20] if '=' in url_str else 'unknown'
                    pbar.set_postfix({"current": digimon_name, "status": "fetched"})
                else:
                    pbar.set_postfix({"current": "failed", "status": "error"})
                pbar.update(1)
                
                return result
                
        # Create session and fetch all pages
        async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            # Process in batches to show progress
            batch_size = 50  # Process in smaller batches for better progress updates
            results = []
            
            with tqdm(total=len(urls), desc="Fetching HTML content", unit="pages") as pbar:
                for i in range(0, len(urls), batch_size):
                    batch_urls = urls[i:i + batch_size]
                    batch_tasks = [fetch_with_delay(session, url, pbar) for url in batch_urls]
                    
                    # Wait for batch to complete
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    # Process results
                    for result in batch_results:
                        if isinstance(result, Exception):
                            logger.error(f"Exception in batch: {result}")
                            continue
                        results.append(result)
                    
        # Process results and save files
        logger.info("Processing and saving scraped data...")
        
        saved_count = 0
        failed_saves = 0
        
        with tqdm(total=len(results), desc="Saving HTML files", unit="files") as save_pbar:
            for url, html in results:
                if html:
                    try:
                        # Save HTML
                        file_path = self.save_html(url, html)
                        self.scraped_urls.append(url)
                        saved_count += 1
                        
                        # Try to extract and download image
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Find image - try multiple selectors
                        img_selectors = [
                            'img.c-digimon__image',
                            'img[alt*="digimon" i]',
                            '.digimon-image img',
                            'article img',
                            'main img[src*="/cimages/digimon/"]'
                        ]
                        
                        img_tag = None
                        for selector in img_selectors:
                            img_tag = soup.select_one(selector)
                            if img_tag and img_tag.get('src'):
                                break
                        
                        if img_tag and img_tag.get('src'):
                            img_url = urljoin(url, img_tag['src'])
                            
                            # Get Digimon name for image filename
                            name_elem = soup.select_one('.c-titleSet__main')
                            if name_elem:
                                name = name_elem.text.strip()
                                self.download_image(img_url, name)
                                
                        save_pbar.set_postfix({"saved": saved_count, "failed": failed_saves})
                        
                    except Exception as e:
                        logger.error(f"Error processing {url}: {e}")
                        self.failed_urls.append((url, str(e)))
                        failed_saves += 1
                        
                elif url:  # URL exists but no content
                    if not any(url in failed[0] for failed in self.failed_urls):
                        self.failed_urls.append((url, "No content returned"))
                        
                save_pbar.update(1)
                
        # Summary
        summary = {
            "total": len(urls),
            "success": len(self.scraped_urls),
            "failed": len(self.failed_urls),
            "failed_urls": self.failed_urls
        }
        
        # Save summary
        with open(self.html_dir.parent / "scrape_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Final report
        logger.info("="*60)
        logger.info(f"Scraping complete!")
        logger.info(f"Total URLs processed: {summary['total']}")
        logger.info(f"Successfully fetched: {len(results)}")
        logger.info(f"Successfully saved: {summary['success']} ({summary['success']/summary['total']*100:.1f}% of total)")
        logger.info(f"Failed to fetch: {summary['total'] - len(results)}")
        logger.info(f"Failed to save: {len(results) - summary['success']}")
        logger.info(f"Total failures: {summary['failed']}")
        
        if summary['failed'] > 0:
            logger.info(f"\nFailure details (first 10):")
            for url, error in self.failed_urls[:10]:
                logger.info(f"  - {url}: {error}")
                
        logger.info("="*60)
        
        return summary