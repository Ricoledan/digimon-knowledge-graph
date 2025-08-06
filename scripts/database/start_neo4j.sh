#!/bin/bash
# Start Neo4j database with health checks

echo "Starting Neo4j database..."
echo "============================"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker is not running. Please start Docker first."
    exit 1
fi

# Start Neo4j
echo "Starting Neo4j container..."
docker-compose up -d neo4j

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker-compose exec -T neo4j cypher-shell -u neo4j -p digimon123 "RETURN 1" &> /dev/null 2>&1; then
        echo ""
        echo "[OK] Neo4j is ready!"
        echo ""
        echo "Access Neo4j Browser at: http://localhost:7474"
        echo "Username: neo4j"
        echo "Password: digimon123"
        echo ""
        echo "Bolt URL: bolt://localhost:7687"
        exit 0
    fi
    
    echo -n "."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done

echo ""
echo "ERROR: Neo4j failed to start within 60 seconds"
echo ""
echo "Check logs with: docker-compose logs neo4j"
exit 1