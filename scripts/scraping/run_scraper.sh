#!/bin/bash
# Run the Digimon scraper with options

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "🦖 Digimon Scraper"
echo "=================="

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ] && [ ! -n "$IN_NIX_SHELL" ]; then
    if [ -f "venv/bin/activate" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    elif command -v poetry &> /dev/null; then
        echo "Activating Poetry environment..."
        poetry run python -m src.scraper.main "$@"
        exit $?
    fi
fi

# Run with any passed arguments
python -m src.scraper.main "$@"