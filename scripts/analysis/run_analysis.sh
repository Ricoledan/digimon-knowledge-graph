#!/bin/bash
# Run analysis on the graph data

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "Running Graph Analysis"
echo "========================"

# Check if Neo4j is running
if ! docker-compose ps neo4j | grep -q "Up"; then
    echo "ERROR: Neo4j is not running. Start it first with:"
    echo "   ./scripts/database/start_neo4j.sh"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ] && [ ! -n "$IN_NIX_SHELL" ]; then
    if [ -f "venv/bin/activate" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    elif command -v poetry &> /dev/null; then
        echo "Using Poetry environment..."
        poetry run python -m src.analysis.main "$@"
        exit $?
    fi
fi

echo "Running analysis modules..."
python -m src.analysis.main "$@"