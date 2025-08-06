# Digimon Knowledge Graph Project

A comprehensive knowledge graph built from digimon.net/reference to analyze relationships between Digimon based on their characteristics, evolution patterns, and shared attributes.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/project-yggdrasil.git
cd project-yggdrasil

# Run the interactive setup
./scripts/run.sh
# Choose option 1 for initial setup

# Or manually:
./scripts/setup/init.sh          # Install dependencies & start Neo4j
./scripts/scraping/investigate_structure.sh  # Analyze HTML structure
./scripts/scraping/run_scraper.sh           # Start scraping
```

That's it! The interactive menu (`./scripts/run.sh`) guides you through everything.

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- One of: Nix (recommended), Poetry, or standard pip/venv

## Environment Setup

#### Option 1: Nix (Recommended)
```bash
# Install Nix if you haven't already
curl -L https://nixos.org/nix/install | sh

# Enable flakes (add to ~/.config/nix/nix.conf)
experimental-features = nix-command flakes

# Enter development shell
nix develop

# Or with direnv
direnv allow
```

#### Option 2: Poetry
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate shell
poetry shell
```

#### Option 3: pyenv + virtualenv
```bash
# Install Python 3.11 with pyenv
pyenv install 3.11.8
pyenv local 3.11.8

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Option 4: Standard virtualenv
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Complete Pipeline

```bash
# 1. Scrape data
python -m src.scraper.main

# 2. Process and translate
python -m src.processor.main

# 3. Load into Neo4j
python -m src.graph.loader

# 4. Run analysis
python -m src.analysis.main
```

## Project Structure

```
digimon-knowledge-graph/
├── src/
│   ├── scraper/         # Web scraping modules
│   ├── graph/           # Neo4j integration
│   ├── analysis/        # Network analysis
│   └── utils/           # Shared utilities
├── data/
│   ├── raw/            # Scraped HTML and images
│   ├── processed/      # Parsed JSON data
│   └── cache/          # Translation cache
├── notebooks/          # Jupyter notebooks
├── docker-compose.yml  # Neo4j setup
└── flake.nix          # Nix environment
```

## Configuration

Edit `.env` file:
```env
# Scraping settings
SCRAPE_DELAY=1.0  # Be respectful!
MAX_RETRIES=3

# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=digimon123
```

## Neo4j Queries

### Basic Queries
```cypher
// Count all Digimon
MATCH (d:Digimon) RETURN count(d);

// Find evolution chains
MATCH path = (d1:Digimon)-[:EVOLVES_FROM*]->(d2:Digimon)
WHERE NOT (d1)<-[:EVOLVES_FROM]-()
RETURN path;

// Most connected Digimon
MATCH (d:Digimon)-[r]-(other)
RETURN d.name, COUNT(DISTINCT other) as connections
ORDER BY connections DESC
LIMIT 10;
```

## Development

### Run Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
ruff check src/
```

### Type Checking
```bash
mypy src/
```

### Jupyter Notebooks
```bash
# Run locally after activating your Python environment
jupyter notebook
# Or with JupyterLab
jupyter lab
```

## Docker Services

- **Neo4j**: Graph database (ports 7474, 7687)
- **Neo4j Browser**: Web UI at http://localhost:7474

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection string | `bolt://localhost:7687` |
| `SCRAPE_DELAY` | Seconds between requests | `1.0` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `DEBUG` | Enable debug mode | `false` |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file

## Author

Ricardo Ledan <ricardoledan@proton.me>

## Acknowledgments

- Data source: [digimon.net/reference](https://digimon.net/reference/)
- Built with Neo4j, Python, and lots of coffee