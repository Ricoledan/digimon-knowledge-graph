#!/bin/bash
# Backup Neo4j database

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="neo4j_backup_${TIMESTAMP}"

echo "Installing Backing up Neo4j database..."
echo "=============================="

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if Neo4j is running
if ! docker-compose ps neo4j | grep -q "Up"; then
    echo "ERROR: Neo4j is not running"
    exit 1
fi

# Create backup using Neo4j admin
echo "Creating backup: $BACKUP_NAME"
docker-compose exec -T neo4j neo4j-admin dump \
    --database=neo4j \
    --to="/backups/${BACKUP_NAME}.dump"

# Copy backup to local directory
docker cp "digimon-neo4j:/backups/${BACKUP_NAME}.dump" "$BACKUP_DIR/"

if [ -f "$BACKUP_DIR/${BACKUP_NAME}.dump" ]; then
    echo "[OK] Backup created successfully: $BACKUP_DIR/${BACKUP_NAME}.dump"
    
    # Clean up old backups (keep last 7)
    echo "Cleaning up old backups..."
    ls -t "$BACKUP_DIR"/*.dump 2>/dev/null | tail -n +8 | xargs -r rm
    
    echo "[OK] Backup complete!"
else
    echo "ERROR: Backup failed"
    exit 1
fi