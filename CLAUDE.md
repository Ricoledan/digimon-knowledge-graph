# Project Yggdrasil - Digimon Knowledge Graph

## Overview
This project builds a comprehensive knowledge graph from digimon.net/reference to analyze relationships between Digimon based on their characteristics, evolution patterns, and shared attributes. The data is scraped from the Japanese reference site, translated to English, and loaded into a Neo4j graph database for network analysis.

## Current Status
- **Phase**: Complete data pipeline ready for production run
- **Environment**: Development environment configured with Nix/Poetry/pip options
- **Database**: Neo4j available via Docker Compose
- **Progress**:
  ✅ HTML structure investigation complete
  ✅ Found 1,249 Digimon URLs via API
  ✅ Scraper successfully tested with 10 Digimon
  ✅ Parser extracting all data correctly
  ✅ Translation pipeline operational with caching
  ✅ Neo4j loader implemented and tested
  ⏳ Ready to run full pipeline (~2-3 hours total)
  ⏳ Analysis queries need implementation

## Key Commands

### Initial Setup
```bash
# Enter development environment
nix develop

# Install CLI
pip install -e .

# First time setup
ygg init  # Starts Neo4j and runs full pipeline
```

### Data Pipeline
```bash
# Check current status
ygg status

# Run data pipeline (~2-3 hours total, no analysis)
ygg run

# Or run individual steps:
ygg scrape       # ~40-50 minutes for all 1,249 Digimon
ygg parse        # ~5 minutes
ygg translate    # ~60-90 minutes
ygg load         # ~5 minutes
ygg analyze      # Run analysis separately
```

### Quick Test Commands
```bash
# Test scraper with small batch (10 Digimon)
python test_scraper_small.py

# Parse scraped HTML files
python -m src.parser.main --test
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
ygg start        # Start Neo4j
ygg stop         # Stop Neo4j
ygg logs         # View Neo4j logs
ygg db-status    # Check Neo4j status

# Data management
ygg prune        # Clean up data files
ygg prune --include-neo4j  # Clean up data files AND Neo4j database
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

## Implementation Details

### Discovered Selectors
From the HTML investigation, the key selectors are:
- **Japanese name**: `.c-titleSet__main`
- **English name**: `.c-titleSet__sub`
- **Level/Type/Attribute**: `dl` (definition lists)
- **Main image**: `.c-thumb img`
- **Profile text**: In structured sections
- **Special moves**: Extracted from profile text
- **Related Digimon**: Links in page content

### Data Extracted
Each Digimon page provides:
- Japanese and English names
- Level (究極体, 完全体, etc.)
- Type (マシーン型, サイボーグ型, etc.)
- Attribute (ワクチン, ウィルス, データ)
- Full profile description (Japanese)
- Special move names
- Related Digimon with links
- Main image URL

## Current Implementation Status
- ✅ Project structure created
- ✅ Configuration system ready
- ✅ Logging and utilities implemented
- ✅ Scraping framework operational
- ✅ HTML structure investigation complete
- ✅ Data extraction parser working
- ✅ Found all 1,249 Digimon URLs
- ✅ Translation pipeline with caching
- ✅ Neo4j schema and loader ready
- ⏳ Full dataset collection (ready to run)
- ⏳ Analysis queries and visualization

## Translation Details
The translation pipeline includes:
- **Google Translate API** via googletrans library
- **Intelligent caching** to avoid repeated API calls
- **Static translations** for common terms (levels, attributes)
- **Rate limiting** to respect API limits
- **Batch processing** for efficiency

Translations provided:
- Level names (究極体 → Mega, 完全体 → Ultimate, etc.)
- Types (マシーン型 → Machine Type)
- Attributes (ワクチン → Vaccine, ウィルス → Virus, データ → Data)
- Full profile descriptions
- Special move names

## Neo4j Graph Schema

### Nodes
- **Digimon**: Main entity with Japanese/English names, profile, etc.
- **Level**: Evolution level (Baby, Rookie, Champion, Ultimate, Mega, etc.)
- **Type**: Digimon type (Machine, Dragon, Beast, etc.)
- **Attribute**: Vaccine, Virus, Data, Free, etc.
- **Move**: Special moves/techniques

### Relationships
- `(Digimon)-[:HAS_LEVEL]->(Level)`
- `(Digimon)-[:HAS_TYPE]->(Type)`
- `(Digimon)-[:HAS_ATTRIBUTE]->(Attribute)`
- `(Digimon)-[:CAN_USE]->(Move)`
- `(Digimon)-[:RELATED_TO]->(Digimon)`
- `(Digimon)-[:SHARES_TYPE]->(Digimon)`
- `(Digimon)-[:SHARES_LEVEL]->(Digimon)`
- `(Digimon)-[:SHARES_ATTRIBUTE]->(Digimon)`
- `(Digimon)-[:SHARES_MOVE]->(Digimon)`

## Next Actions
1. Run full scraper for all 1,249 Digimon (~40-50 minutes)
2. Parse all HTML files to extract structured data
3. Translate all Digimon data (with caching for efficiency)
4. Configure Neo4j schema and relationships
5. Load data into graph database
6. Create analysis queries and visualizations

## Full Pipeline Command Sequence
```bash
# Option 1: Run data pipeline (without analysis)
ygg init  # First time (starts Neo4j + data pipeline)
# or
ygg run   # If Neo4j is already running (data pipeline only)

# Option 2: Run steps individually
ygg start        # Start Neo4j
ygg scrape       # Scrape all Digimon (~40-50 minutes)
ygg parse        # Parse all HTML files
ygg translate    # Translate all data
ygg load         # Load into Neo4j
ygg analyze      # Run analysis (separate command)
```

## Notes for Claude
- This is a data analysis project focused on creating a knowledge graph
- The scraper is designed to be respectful (rate limiting, robots.txt)
- Translation caching is important to avoid API limits
- File naming needs special handling for Japanese characters
- The project uses defensive security practices only

## Pipeline Validation
Run `python check_status.py` to see the current state of the pipeline and what steps are needed next.

## Estimated Time for Full Pipeline
1. **Scraping**: ~40-50 minutes (1,249 pages with 1s delay)
2. **Parsing**: ~5 minutes
3. **Translation**: ~60-90 minutes (with caching and rate limiting)
4. **Neo4j Loading**: ~5 minutes
5. **Total**: ~2-3 hours

## Success Metrics
- All 1,249 Digimon scraped and parsed
- 100% translation coverage with caching
- Complete graph with all relationships
- Analysis reveals network patterns and insights