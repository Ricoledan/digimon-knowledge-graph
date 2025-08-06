#!/bin/bash
# Resume interrupted scraping session

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "Resume Scraping"
echo "=================="

# Check for previous scraping summary
if [ ! -f "data/raw/scrape_summary.json" ]; then
    echo "ERROR: No previous scraping session found"
    echo "Start a new scraping session with:"
    echo "  ./scripts/scraping/run_scraper.sh"
    exit 1
fi

# Display previous session info
echo "Previous session summary:"
if command -v jq &> /dev/null; then
    jq '{total, success, failed}' data/raw/scrape_summary.json
else
    cat data/raw/scrape_summary.json
fi

echo ""
echo "TODO: Implement resume functionality"
echo "This will skip already downloaded pages and retry failed ones"