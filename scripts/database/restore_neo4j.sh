#!/bin/bash
# Restore Neo4j database from backup

echo "Restoring Neo4j database"
echo "========================"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -la ./backups/*.dump 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Check if Neo4j is running
if ! docker-compose ps neo4j | grep -q "Up"; then
    echo "ERROR: Neo4j is not running. Start it first with:"
    echo "   ./scripts/database/start_neo4j.sh"
    exit 1
fi

echo "WARNING: This will replace the current database!"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop Neo4j
echo "Stopping Neo4j..."
docker-compose stop neo4j

# Copy backup to container
BACKUP_NAME=$(basename "$BACKUP_FILE")
docker cp "$BACKUP_FILE" "digimon-neo4j:/var/lib/neo4j/import/${BACKUP_NAME}"

# Start Neo4j and restore
echo "Starting Neo4j and restoring..."
docker-compose run --rm neo4j neo4j-admin load \
    --from="/var/lib/neo4j/import/${BACKUP_NAME}" \
    --database=neo4j \
    --force

# Start Neo4j normally
docker-compose up -d neo4j

echo "[OK] Restore complete! Neo4j is restarting..."
echo "Wait a moment then access at: http://localhost:7474"