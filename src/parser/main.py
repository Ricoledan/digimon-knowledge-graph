#!/usr/bin/env python3
"""Main entry point for the Digimon HTML parser."""

import sys
from pathlib import Path

from loguru import logger

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.parser.html_parser import DigimonParser


def main():
    """Run the parser on all HTML files."""
    logger.info("Starting Digimon HTML Parser")
    logger.info("This will extract structured data from all scraped HTML files")
    
    parser = DigimonParser()
    
    try:
        # Parse all files
        summary = parser.parse_all_files()
        
        # Check if we had any successes
        if summary['successful'] == 0:
            logger.error("No files were successfully parsed!")
            sys.exit(1)
            
        logger.info(f"\nParsing completed successfully!")
        logger.info(f"Check {summary['output_directory']} for the extracted JSON files")
        
    except KeyboardInterrupt:
        logger.warning("Parsing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()