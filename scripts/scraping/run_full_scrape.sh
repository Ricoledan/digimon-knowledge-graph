#!/usr/bin/env bash
# Run the full scraping pipeline with progress monitoring

set -e

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

echo "========================================"
echo "Digimon Full Scraping Pipeline"
echo "========================================"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if we already have API data
if [ -f "data/raw/html/_all_digimon_urls.json" ]; then
    TOTAL_URLS=$(jq '.total_urls' "data/raw/html/_all_digimon_urls.json" 2>/dev/null || echo "0")
    echo "Found existing API data with $TOTAL_URLS URLs"
    echo ""
    
    read -p "Use existing API data? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Fetching fresh data from API..."
        python -m src.scraper.api_fetcher
    fi
else
    echo "No API data found. Fetching from API first..."
    python -m src.scraper.api_fetcher
fi

echo ""
echo "Starting main scraper with progress monitoring..."
echo "This will show real-time progress with ETA"
echo ""

# Run the scraper with API URLs
python -m src.scraper.main --use-api-urls

echo ""
echo "Scraping pipeline complete!"
echo ""

# Show final statistics
if [ -f "data/raw/scrape_summary.json" ]; then
    echo "Final Statistics:"
    jq '.' "data/raw/scrape_summary.json"
fi

# Count files
HTML_COUNT=$(find "data/raw/html" -name "*.html" -not -name "_*.html" | wc -l | tr -d ' ')
IMG_COUNT=$(find "data/raw/images" -name "*" -type f | wc -l | tr -d ' ')

echo ""
echo "Files created:"
echo "- HTML files: $HTML_COUNT"
echo "- Images: $IMG_COUNT"
echo ""
echo "Next steps:"
echo "1. Run parser to extract structured data: python -m src.parser.main"
echo "2. Translate Japanese content: python -m src.translator.main"
echo "3. Load into Neo4j: python -m src.graph.loader"