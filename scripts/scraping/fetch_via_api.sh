#!/usr/bin/env bash
# Fetch all Digimon data using the discovered API endpoint

set -e

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

echo "========================================"
echo "Digimon API Data Fetcher"
echo "========================================"
echo ""
echo "This will fetch all Digimon data using the API endpoint"
echo "discovered from the index page."
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Run the API fetcher
echo "Fetching Digimon data via API..."
python -m src.scraper.api_fetcher

echo ""
echo "API fetch complete!"
echo ""
echo "Next steps:"
echo "1. Check data/raw/api_data/ for the fetched data"
echo "2. Run the traditional scraper with the generated URLs:"
echo "   python -m src.scraper.main --use-api-urls"
echo ""