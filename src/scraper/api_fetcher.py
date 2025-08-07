#!/usr/bin/env python3
"""Fetch Digimon data using the API endpoint discovered from the index page."""

import json
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin
import requests
from loguru import logger
from pathlib import Path

from ..utils.config import config
from ..utils.file_utils import ensure_directory


class DigimonAPIFetcher:
    """Fetch Digimon data using the discovered API endpoint."""
    
    def __init__(self):
        """Initialize API fetcher."""
        self.base_url = "https://digimon.net/reference/"
        self.api_endpoint = urljoin(self.base_url, "request.php")
        self.detail_url_template = urljoin(self.base_url, "detail.php?directory_name={}")
        
        self.headers = {
            "User-Agent": config.get("scraping.user_agent"),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": urljoin(self.base_url, "index.php")
        }
        
        self.delay = config.get("scraping.delay", 1.0)
        self.data_dir = Path(config.get("paths.raw_html")).parent / "api_data"
        ensure_directory(self.data_dir)
        
    def fetch_batch(self, offset: int = 0, **search_params) -> Optional[Dict]:
        """Fetch a batch of Digimon data from the API.
        
        Args:
            offset: The offset for pagination
            **search_params: Additional search parameters
            
        Returns:
            API response data or None if failed
        """
        params = {
            "digimon_name": search_params.get("digimon_name", ""),
            "name": search_params.get("name", ""),
            "digimon_level": search_params.get("digimon_level", ""),
            "attribute": search_params.get("attribute", ""),
            "type": search_params.get("type", ""),
            "next": str(offset),
            "view_more": "true" if offset > 0 else None
        }
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        try:
            logger.info(f"Fetching batch with offset: {offset}")
            response = requests.get(
                self.api_endpoint,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            # The response should be JSON
            data = response.json()
            return data
            
        except requests.exceptions.JSONDecodeError:
            logger.error(f"Response was not valid JSON: {response.text[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Error fetching batch at offset {offset}: {e}")
            return None
            
    def fetch_all_digimon(self) -> List[Dict]:
        """Fetch all Digimon data by paginating through the API.
        
        Returns:
            List of all Digimon data
        """
        all_digimon = []
        offset = 0
        batch_count = 0
        
        logger.info("Starting to fetch all Digimon data via API...")
        
        while True:
            # Respect rate limit
            if batch_count > 0:
                time.sleep(self.delay)
                
            # Fetch batch
            data = self.fetch_batch(offset)
            
            if not data:
                logger.error(f"Failed to fetch batch at offset {offset}")
                break
                
            # Extract Digimon list from response
            # The structure is: {"rows": [...], "next": offset_or_-1}
            digimon_list = data.get("rows", [])
            next_offset = data.get("next", -1)
            
            if not digimon_list and isinstance(data, list):
                # Sometimes the response might be a direct list
                digimon_list = data
                next_offset = -1  # Assume no more data
                
            logger.info(f"Batch {batch_count + 1}: Found {len(digimon_list)} Digimon")
            
            # Add to our collection
            all_digimon.extend(digimon_list)
            
            # Save batch data for debugging
            batch_file = self.data_dir / f"batch_{batch_count:03d}.json"
            with open(batch_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            batch_count += 1
            
            # Check if there's more data
            if next_offset == -1 or next_offset == "-1":
                logger.info("No more data available (next = -1)")
                break
                
            # Update offset for next batch
            offset = int(next_offset)
            
            # Safety check to prevent infinite loops
            if batch_count > 100:
                logger.warning("Reached 100 batches, stopping to prevent infinite loop")
                break
                
        logger.info(f"Fetched {len(all_digimon)} Digimon in {batch_count} batches")
        
        # Save complete list
        output_file = self.data_dir / "all_digimon.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total": len(all_digimon),
                "digimon": all_digimon,
                "batches": batch_count
            }, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved complete Digimon list to {output_file}")
        
        # Generate URLs for traditional scraper
        self.generate_detail_urls(all_digimon)
        
        return all_digimon
        
    def generate_detail_urls(self, digimon_list: List[Dict]) -> List[str]:
        """Generate detail page URLs from the Digimon data.
        
        Args:
            digimon_list: List of Digimon data from API
            
        Returns:
            List of detail page URLs
        """
        urls = []
        
        for digimon in digimon_list:
            # Look for directory_name which is used in the detail URL
            directory_name = digimon.get("directory_name")
            if directory_name:
                url = self.detail_url_template.format(directory_name)
                urls.append(url)
                
        # Save URLs for the traditional scraper
        urls_file = Path(config.get("paths.raw_html")) / "_all_digimon_urls.json"
        with open(urls_file, 'w', encoding='utf-8') as f:
            json.dump({
                "source": "api",
                "total_urls": len(urls),
                "urls": urls
            }, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Generated {len(urls)} detail URLs and saved to {urls_file}")
        
        return urls


def main():
    """Run the API fetcher."""
    fetcher = DigimonAPIFetcher()
    digimon_data = fetcher.fetch_all_digimon()
    
    if digimon_data:
        logger.info(f"Successfully fetched {len(digimon_data)} Digimon")
        
        # Print sample data
        if digimon_data:
            logger.info("Sample Digimon data:")
            sample = digimon_data[0]
            for key, value in sample.items():
                logger.info(f"  {key}: {value}")
    else:
        logger.error("Failed to fetch Digimon data")


if __name__ == "__main__":
    main()