#!/usr/bin/env python3
"""Main entry point for the Digimon scraper."""

import argparse
import asyncio
import sys
import time
from pathlib import Path

from loguru import logger

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.scraper.fetcher import DigimonScraper
from src.utils.config import config


def main():
    """Run the scraper."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scrape Digimon data from digimon.net")
    parser.add_argument(
        "--use-api-urls",
        action="store_true",
        help="Use URLs generated from API fetch instead of scraping index"
    )
    parser.add_argument(
        "--fetch-api-first",
        action="store_true",
        help="Fetch data via API before scraping individual pages"
    )
    args = parser.parse_args()
    
    logger.info("Starting Digimon Knowledge Graph Scraper")
    
    # If requested, fetch via API first
    if args.fetch_api_first:
        logger.info("Fetching data via API first...")
        from src.scraper.api_fetcher import DigimonAPIFetcher
        api_fetcher = DigimonAPIFetcher()
        api_fetcher.fetch_all_digimon()
        args.use_api_urls = True  # Automatically use the generated URLs
    
    # Check if we should use async
    use_async = config.get("scraping.concurrent_requests", 1) > 1
    
    scraper = DigimonScraper()
    
    # Track timing
    start_time = time.time()
    
    try:
        if use_async:
            logger.info("Using async scraping for better performance")
            logger.info(f"Starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            summary = asyncio.run(scraper.scrape_all_async(use_api_urls=args.use_api_urls))
        else:
            logger.info("Using synchronous scraping")
            logger.info(f"Starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            summary = scraper.scrape_all(use_api_urls=args.use_api_urls)
            
        # Calculate duration
        duration = time.time() - start_time
        minutes, seconds = divmod(int(duration), 60)
        hours, minutes = divmod(minutes, 60)
        
        # Report results
        logger.info(f"\nScraping completed in {hours}h {minutes}m {seconds}s")
        logger.info(f"Average time per URL: {duration/summary['total']:.2f}s")
        
        # Summary already logged by fetcher, just add timing info
        logger.info(f"Finished at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()