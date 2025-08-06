#!/bin/bash
# Investigate HTML structure of Digimon pages

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "Checking HTML Structure Investigator"
echo "============================="

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ] && [ ! -n "$IN_NIX_SHELL" ]; then
    if [ -f "venv/bin/activate" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    elif command -v poetry &> /dev/null; then
        echo "Using Poetry environment..."
        poetry run python -m src.scraper.investigator "$@"
        exit $?
    fi
fi

echo "Analyzing digimon.net HTML structure..."
echo ""

python -m src.scraper.investigator "$@"

# Check if investigation results exist
if [ -f "data/investigation_results.json" ]; then
    echo ""
    echo "[OK] Investigation complete!"
    echo "Results saved to: data/investigation_results.json"
    echo ""
    echo "You can review the results with:"
    echo "  cat data/investigation_results.json | jq '.recommendations'"
fi