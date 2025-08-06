# Scripts Directory

Organized scripts for the Digimon Knowledge Graph project.

## Directory Structure

```
scripts/
├── setup/          # Project setup and dependency management
├── database/       # Neo4j database operations
├── scraping/       # Web scraping operations
└── analysis/       # Data analysis and export
```

## Setup Scripts

### `setup/init.sh`
Complete project initialization including directories, dependencies, and services.
```bash
./scripts/setup/init.sh
```

### `setup/check_requirements.sh`
Check if all required system dependencies are installed.
```bash
./scripts/setup/check_requirements.sh
```

### `setup/install_deps.sh`
Install Python dependencies using the best available method (Nix, Poetry, pyenv, or venv).
```bash
./scripts/setup/install_deps.sh
```

## Database Scripts

### `database/start_neo4j.sh`
Start Neo4j database with health checks.
```bash
./scripts/database/start_neo4j.sh
```

### `database/backup_neo4j.sh`
Create a backup of the Neo4j database.
```bash
./scripts/database/backup_neo4j.sh
```

### `database/restore_neo4j.sh`
Restore Neo4j database from a backup file.
```bash
./scripts/database/restore_neo4j.sh ./backups/neo4j_backup_20240320_120000.dump
```

## Scraping Scripts

### `scraping/investigate_structure.sh`
Analyze the HTML structure of digimon.net to determine proper selectors.
```bash
./scripts/scraping/investigate_structure.sh
```

### `scraping/run_scraper.sh`
Run the main web scraper.
```bash
./scripts/scraping/run_scraper.sh
```

### `scraping/resume_scraping.sh`
Resume an interrupted scraping session.
```bash
./scripts/scraping/resume_scraping.sh
```

## Analysis Scripts

### `analysis/run_analysis.sh`
Run graph analysis on the Neo4j data.
```bash
./scripts/analysis/run_analysis.sh
```

### `analysis/export_results.sh`
Export analysis results in various formats.
```bash
./scripts/analysis/export_results.sh csv
./scripts/analysis/export_results.sh json
./scripts/analysis/export_results.sh graphml
./scripts/analysis/export_results.sh all
```

## Making Scripts Executable

All scripts need to be made executable before first use:
```bash
chmod +x scripts/**/*.sh
```

## Common Workflows

### First Time Setup
```bash
./scripts/setup/check_requirements.sh
./scripts/setup/init.sh
```

### Daily Workflow
```bash
# Start database
./scripts/database/start_neo4j.sh

# Run scraper
./scripts/scraping/run_scraper.sh

# Analyze data
./scripts/analysis/run_analysis.sh

# Backup when done
./scripts/database/backup_neo4j.sh
```

### Investigation Mode
```bash
# First investigate the HTML structure
./scripts/scraping/investigate_structure.sh

# Review results
cat data/investigation_results.json | jq '.recommendations'

# Update config.yaml with correct selectors
# Then run scraper
./scripts/scraping/run_scraper.sh
```