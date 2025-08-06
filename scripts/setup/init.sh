#!/bin/bash
set -e

echo "Setting up Digimon Knowledge Graph Project"
echo "==========================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    exit 1
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is required but not installed."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "[OK] .env file created. Please review and update as needed."
fi

# Create directories
echo "Creating project directories..."
mkdir -p data/{raw/{html,images},processed/digimon,translations,cache,neo4j/{data,logs,import,plugins}}
mkdir -p logs backups

# Install Python dependencies
echo "Installing Python dependencies..."
if command -v poetry &> /dev/null; then
    echo "Using Poetry..."
    poetry install
elif [ -f "venv/bin/activate" ]; then
    echo "Using existing virtual environment..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Start Neo4j
echo "Starting Neo4j database..."
docker-compose up -d neo4j

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to start..."
for i in {1..30}; do
    if docker-compose exec -T neo4j cypher-shell -u neo4j -p digimon123 "RETURN 1" &> /dev/null; then
        echo "[OK] Neo4j is ready!"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your settings"
echo "2. Run the structure investigator to analyze HTML:"
echo "   python -m src.scraper.investigator"
echo "3. Start scraping:"
echo "   python -m src.scraper.main"
echo "4. Access Neo4j Browser at http://localhost:7474"
echo "   (username: neo4j, password: digimon123)"
echo ""
echo "For Jupyter notebooks:"
echo "   jupyter notebook"
echo ""