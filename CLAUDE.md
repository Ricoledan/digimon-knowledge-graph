# Project Yggdrasil - Digimon Knowledge Graph

## Overview
This project builds a comprehensive knowledge graph from digimon.net/reference to analyze relationships between Digimon based on their characteristics, evolution patterns, and shared attributes. The data is scraped from the Japanese reference site, translated to English, and loaded into a Neo4j graph database for network analysis.

## Current Status
- **Phase**: Initial setup complete, ready for data scraping
- **Environment**: Development environment configured with Nix/Poetry/pip options
- **Database**: Neo4j available via Docker Compose
- **Updates Made**:
  - Added robots.txt compliance checking
  - Updated scraper to start from index page: https://digimon.net/reference/index.php
  - Added HTML structure investigation tools
- **Next Step**: Run HTML structure investigation to identify correct selectors

## Key Commands

### Initial Setup
```bash
./scripts/run.sh  # Interactive menu for all operations
```

### Data Pipeline
```bash
# 1. Investigate HTML structure (do this first!)
./scripts/scraping/investigate_structure.sh

# 2. Run the scraper
./scripts/scraping/run_scraper.sh

# 3. Process and translate data
python -m src.processor.main

# 4. Load into Neo4j
python -m src.graph.loader

# 5. Run analysis
python -m src.analysis.main
```

### Development Commands
```bash
# Testing
pytest tests/

# Code quality
black src/
ruff check src/
mypy src/

# Neo4j operations
./scripts/database/start_neo4j.sh
./scripts/database/backup_neo4j.sh
```

## Architecture

### Data Flow
1. **Scraper** → Fetches HTML pages from digimon.net/reference
2. **Parser** → Extracts structured data from HTML
3. **Translator** → Translates Japanese content to English
4. **Loader** → Imports data into Neo4j graph database
5. **Analyzer** → Performs network analysis and generates insights

### Key Technologies
- **Scraping**: BeautifulSoup4, requests, asyncio
- **Translation**: googletrans (with caching)
- **Database**: Neo4j Community Edition
- **Analysis**: NetworkX, pandas, matplotlib

### Graph Schema
- **Nodes**: Digimon, Type, Attribute, Level, Move
- **Relationships**: EVOLVES_FROM, HAS_TYPE, HAS_ATTRIBUTE, CAN_USE, SHARES_*

## Important Configuration

### Environment Variables (.env)
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=digimon123
SCRAPE_DELAY=1.0
```

### Scraping Settings (config.yaml)
- Base URL: https://digimon.net/reference/
- Rate limit: 1 second delay between requests
- Concurrent requests: 3
- Respects robots.txt

## Project Goals
1. Create comprehensive Digimon knowledge graph
2. Analyze evolution patterns and relationships
3. Discover insights through network analysis
4. Publish findings in technical article

## Current Implementation Status
- ✅ Project structure created
- ✅ Configuration system ready
- ✅ Logging and utilities implemented
- ✅ Scraping framework in place
- ⏳ HTML structure investigation needed
- ⏳ Data extraction and parsing
- ⏳ Translation pipeline
- ⏳ Neo4j integration
- ⏳ Analysis and visualization

## Next Actions
1. Run HTML structure investigation to map CSS selectors
2. Execute initial scraping run
3. Verify data extraction accuracy
4. Set up translation caching
5. Begin loading data into Neo4j

## Notes for Claude
- This is a data analysis project focused on creating a knowledge graph
- The scraper is designed to be respectful (rate limiting, robots.txt)
- Translation caching is important to avoid API limits
- File naming needs special handling for Japanese characters
- The project uses defensive security practices only