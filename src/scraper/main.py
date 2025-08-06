#!/usr/bin/env python3
"""Main entry point for the Digimon scraper."""

import asyncio
import sys
from pathlib import Path

from loguru import logger

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.scraper.fetcher import DigimonScraper
from src.utils.config import config


def main():
    """Run the scraper."""
    logger.info("Starting Digimon Knowledge Graph Scraper")
    
    # Check if we should use async
    use_async = config.get("scraping.concurrent_requests", 1) > 1
    
    scraper = DigimonScraper()
    
    try:
        if use_async:
            logger.info("Using async scraping for better performance")
            summary = asyncio.run(scraper.scrape_all_async())
        else:
            logger.info("Using synchronous scraping")
            summary = scraper.scrape_all()
            
        # Report results
        logger.info(f"Scraping completed!")
        logger.info(f"Total URLs: {summary['total']}")
        logger.info(f"Successful: {summary['success']}")
        logger.info(f"Failed: {summary['failed']}")
        
        if summary['failed_urls']:
            logger.warning("Failed URLs:")
            for url, error in summary['failed_urls']:
                logger.warning(f"  - {url}: {error}")
                
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()