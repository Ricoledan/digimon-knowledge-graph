"""Investigate HTML structure of Digimon pages to determine selectors."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger

from ..utils.config import config


class StructureInvestigator:
    """Investigate and analyze HTML structure of Digimon pages."""
    
    def __init__(self):
        """Initialize investigator."""
        self.base_url = config.get("scraping.base_url")
        self.index_url = "https://digimon.net/reference/index.php"
        self.headers = {
            "User-Agent": config.get("scraping.user_agent"),
            "Accept-Language": "ja,en;q=0.9"
        }
        
    def fetch_sample_page(self, url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Fetch a sample page for investigation."""
        if not url:
            # Try to fetch index first to get a sample URL
            url = self.index_url
            
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
            
    def find_digimon_links(self, soup: BeautifulSoup) -> List[str]:
        """Find all possible Digimon detail page links."""
        found_links = {}
        
        # Try various selectors
        selectors = [
            ('a[href*="/detail/"]', 'Links containing /detail/'),
            ('a[href*="/reference/detail/"]', 'Links containing /reference/detail/'),
            ('a.digimon-link', 'Links with class digimon-link'),
            ('.digimon-list a', 'Links inside .digimon-list'),
            ('a[href$=".html"]', 'Links ending with .html'),
            ('main a[href]', 'All links in main content'),
            ('.content a[href]', 'All links in .content'),
        ]
        
        for selector, description in selectors:
            links = soup.select(selector)
            if links:
                found_links[description] = [
                    self._normalize_url(link.get('href', ''))
                    for link in links[:5]  # First 5 as examples
                ]
                logger.info(f"Found {len(links)} links with selector '{selector}'")
                
        return found_links
        
    def analyze_detail_page(self, url: str) -> Dict[str, any]:
        """Analyze a Digimon detail page structure."""
        soup = self.fetch_sample_page(url)
        if not soup:
            return {}
            
        analysis = {
            "url": url,
            "title_elements": {},
            "data_sections": {},
            "image_elements": {},
            "potential_selectors": {}
        }
        
        # Analyze title elements
        title_selectors = [
            '.c-titleSet__main',
            '.c-titleSet__sub',
            'h1',
            'h2',
            '.title',
            '.name',
        ]
        
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                analysis["title_elements"][selector] = {
                    "text": elem.get_text(strip=True),
                    "is_english": self._is_english(elem.get_text(strip=True))
                }
                
        # Look for structured data
        # Check for definition lists, tables, or specific divs
        for dl in soup.find_all('dl'):
            dt_text = dl.find('dt')
            dd_text = dl.find('dd')
            if dt_text and dd_text:
                key = dt_text.get_text(strip=True)
                value = dd_text.get_text(strip=True)
                analysis["data_sections"][key] = value
                
        # Find images
        img_selectors = [
            'img[alt*="digimon" i]',
            'img[alt*="デジモン"]',
            '.digimon-image img',
            '.character-image img',
            'main img',
            'article img',
        ]
        
        for selector in img_selectors:
            imgs = soup.select(selector)
            if imgs:
                analysis["image_elements"][selector] = [
                    {
                        "src": img.get('src', ''),
                        "alt": img.get('alt', ''),
                        "width": img.get('width', 'auto'),
                        "height": img.get('height', 'auto')
                    }
                    for img in imgs[:2]
                ]
                
        # Extract URL information
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if path_parts:
            analysis["url_info"] = {
                "path_parts": path_parts,
                "last_segment": path_parts[-1] if path_parts else None,
                "potential_id": self._extract_id_from_url(url)
            }
            
        return analysis
        
    def _normalize_url(self, url: str) -> str:
        """Normalize relative URLs to absolute."""
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            # Use the index URL's base for absolute paths
            from urllib.parse import urlparse
            parsed = urlparse(self.index_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            return f"{base}{url}"
        else:
            # For relative paths, use the index URL's directory
            return f"{self.index_url.rsplit('/', 1)[0]}/{url}"
            
    def _is_english(self, text: str) -> bool:
        """Check if text is primarily English."""
        try:
            text.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False
            
    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Try to extract a Digimon ID from URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Try different patterns
        if 'detail/' in path:
            parts = path.split('detail/')
            if len(parts) > 1:
                return parts[1].replace('.html', '').replace('/', '_')
                
        # Last resort: use last path segment
        segments = path.split('/')
        if segments:
            return segments[-1].replace('.html', '')
            
        return None
        
    def investigate_structure(self, sample_size: int = 5) -> Dict[str, any]:
        """Perform full structure investigation."""
        logger.info("Starting structure investigation...")
        
        # First, get the index page
        index_soup = self.fetch_sample_page()
        if not index_soup:
            logger.error("Failed to fetch index page")
            return {}
            
        # Find Digimon links
        link_analysis = self.find_digimon_links(index_soup)
        
        # Get sample detail URLs
        sample_urls = []
        for links in link_analysis.values():
            sample_urls.extend(links)
            if len(sample_urls) >= sample_size:
                break
                
        sample_urls = list(set(sample_urls))[:sample_size]
        
        # Analyze detail pages
        detail_analyses = []
        for url in sample_urls:
            logger.info(f"Analyzing: {url}")
            analysis = self.analyze_detail_page(url)
            if analysis:
                detail_analyses.append(analysis)
                
        # Compile results
        investigation_results = {
            "index_page_links": link_analysis,
            "sample_detail_pages": detail_analyses,
            "recommendations": self._generate_recommendations(detail_analyses)
        }
        
        # Save results
        output_path = Path("data/investigation_results.json")
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(investigation_results, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Investigation complete. Results saved to {output_path}")
        
        return investigation_results
        
    def _generate_recommendations(self, analyses: List[Dict]) -> Dict[str, str]:
        """Generate selector recommendations based on analysis."""
        recommendations = {
            "name_selector": ".c-titleSet__main",
            "english_name_selector": ".c-titleSet__sub",
            "image_selector": "img[alt*='digimon' i]",
            "data_container": "dl",
            "notes": []
        }
        
        # Check consistency across pages
        if analyses:
            # Check if all pages have the same title structure
            has_main_title = all(
                ".c-titleSet__main" in a.get("title_elements", {})
                for a in analyses
            )
            has_sub_title = all(
                ".c-titleSet__sub" in a.get("title_elements", {})
                for a in analyses
            )
            
            if has_main_title:
                recommendations["notes"].append("Main title selector is consistent")
            if has_sub_title:
                recommendations["notes"].append("Subtitle (possibly English name) is consistent")
                
        return recommendations


def main():
    """Run the structure investigation."""
    investigator = StructureInvestigator()
    results = investigator.investigate_structure(sample_size=3)
    
    # Print summary
    if results.get("recommendations"):
        logger.info("Recommended selectors:")
        for key, value in results["recommendations"].items():
            if key != "notes":
                logger.info(f"  {key}: {value}")
                
        if results["recommendations"].get("notes"):
            logger.info("Notes:")
            for note in results["recommendations"]["notes"]:
                logger.info(f"  - {note}")


if __name__ == "__main__":
    main()