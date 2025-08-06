# Quick Start Guide

Get the Digimon Knowledge Graph up and running in 5 minutes!

## Prerequisites Check

```bash
# Check if you have everything needed
./scripts/setup/check_requirements.sh
```

## Option 1: Interactive Setup (Recommended)

```bash
# Just run this and follow the menu
./scripts/run.sh
```

Select these options in order:
1. **Option 1** - Initial setup
2. **Option 8** - Investigate HTML structure  
3. **Option 9** - Run scraper
4. **Option 11** - Run analysis

## Option 2: Command Line Setup

```bash
# 1. Initial setup (installs dependencies & starts Neo4j)
./scripts/setup/init.sh

# 2. Investigate website structure
./scripts/scraping/investigate_structure.sh

# 3. Start scraping
./scripts/scraping/run_scraper.sh

# 4. Load data into Neo4j (once parser is implemented)
python -m src.graph.loader

# 5. Run analysis
./scripts/analysis/run_analysis.sh
```

## Option 3: Developer Quick Start

```bash
# For developers who want more control
./scripts/dev.sh start     # Start Neo4j
./scripts/dev.sh shell     # Python REPL with imports
./scripts/dev.sh backup    # Backup database

# Or use the traditional way
source venv/bin/activate   # or: poetry shell / nix develop
python -m src.scraper.investigator
python -m src.scraper.main
```

## Verify Everything is Working

1. **Neo4j Browser**: http://localhost:7474
   - Username: `neo4j`
   - Password: `digimon123`

2. **Check logs**:
   ```bash
   tail -f logs/digimon_kg.log
   ```

3. **View scraped data**:
   ```bash
   ls -la data/raw/html/
   ```

## Next Steps

Once you have data scraped:

1. Update `config.yaml` with correct HTML selectors based on investigation
2. Implement parser module to extract structured data
3. Load data into Neo4j
4. Run analysis and create visualizations
5. Export results for your article

## Troubleshooting

**Neo4j won't start?**
```bash
docker-compose logs neo4j
docker-compose restart neo4j
```

**Permission errors?**
```bash
chmod +x scripts/**/*.sh
```

**Python dependencies issues?**
```bash
# Try a different installation method
./scripts/setup/install_deps.sh
```

**Need help?**
- Check the full README.md
- Review logs in `./logs/`
- Run `./scripts/run.sh` for interactive help