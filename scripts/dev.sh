#!/bin/bash
# Development helper script for common tasks

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Parse command
CMD="${1:-help}"
shift

case "$CMD" in
    start)
        echo "Starting development environment..."
        $SCRIPT_DIR/database/start_neo4j.sh
        ;;
        
    stop)
        echo "Stopping all services..."
        docker-compose down
        ;;
        
    logs)
        SERVICE="${1:-neo4j}"
        docker-compose logs -f "$SERVICE"
        ;;
        
    shell)
        # Python shell with project imports
        python -c "
import sys
sys.path.insert(0, '.')
from src.utils.config import config
from src.utils.logger import logger
print('Available imports: config, logger')
print('Project root:', '$PROJECT_ROOT')
import IPython
IPython.embed()
"
        ;;
        
    test)
        # Run tests
        pytest tests/ "$@"
        ;;
        
    lint)
        # Run linting
        echo "Running black..."
        black src/ --check
        echo "Running ruff..."
        ruff check src/
        ;;
        
    format)
        # Format code
        echo "Formatting with black..."
        black src/
        echo "Fixing with ruff..."
        ruff check src/ --fix
        ;;
        
    clean)
        # Clean up generated files
        echo "Cleaning up..."
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
        find . -type f -name "*.pyc" -delete
        rm -rf .pytest_cache
        rm -rf .mypy_cache
        rm -rf .ruff_cache
        echo "[OK] Cleaned!"
        ;;
        
    neo4j-shell)
        # Open Neo4j cypher shell
        docker-compose exec neo4j cypher-shell -u neo4j -p digimon123
        ;;
        
    backup)
        # Quick backup
        $SCRIPT_DIR/database/backup_neo4j.sh
        ;;
        
    help|*)
        echo "Development Helper Commands:"
        echo ""
        echo "  ./scripts/dev.sh start      - Start development services"
        echo "  ./scripts/dev.sh stop       - Stop all services"
        echo "  ./scripts/dev.sh logs       - View logs (neo4j by default)"
        echo "  ./scripts/dev.sh shell      - Python shell with imports"
        echo "  ./scripts/dev.sh test       - Run tests"
        echo "  ./scripts/dev.sh lint       - Check code style"
        echo "  ./scripts/dev.sh format     - Format code"
        echo "  ./scripts/dev.sh clean      - Clean cache files"
        echo "  ./scripts/dev.sh neo4j-shell - Neo4j cypher shell"
        echo "  ./scripts/dev.sh backup     - Quick database backup"
        echo ""
        ;;
esac