# Quick Start Guide

Get the Digimon Knowledge Graph up and running in 5 minutes!

## Prerequisites Check

```bash
# Check if you have everything needed
docker --version     # Docker required
nix --version        # Nix recommended
python --version     # Python 3.11+
```

## Option 1: Quickest Setup (Recommended)

```bash
# Enter Nix environment
nix develop

# Install CLI 
pip install -e .

# Run everything
ygg init
```

This will:
1. Start Neo4j database
2. Scrape all Digimon data
3. Parse and translate everything
4. Load into Neo4j
5. Run analysis

## Option 2: Step-by-Step Setup

```bash
# 1. Enter Nix environment
nix develop

# 2. Install CLI
pip install -e .

# 3. Check status
ygg status

# 4. Start Neo4j
ygg start

# 5. Run pipeline
ygg run
```

## Option 3: Manual Control

```bash
# Run individual steps
ygg start        # Start Neo4j
ygg scrape       # Scrape data (~40-50 min)
ygg parse        # Parse HTML (~5 min)
ygg translate    # Translate (~60-90 min)  
ygg load         # Load to Neo4j (~5 min)
ygg analyze      # Run analysis

# Other commands
ygg status       # Check progress
ygg prune        # Clean up data
ygg logs         # View Neo4j logs

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