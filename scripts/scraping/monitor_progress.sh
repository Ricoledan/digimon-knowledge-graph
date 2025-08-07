#!/usr/bin/env bash
# Monitor scraping progress

set -e

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

echo "========================================"
echo "Scraping Progress Monitor"
echo "========================================"
echo ""

# Check how many URLs we should scrape
TOTAL_URLS=$(jq '.total_urls' "$PROJECT_ROOT/data/raw/html/_all_digimon_urls.json" 2>/dev/null || echo "0")

# Count scraped HTML files (excluding special files)
SCRAPED=$(find "$PROJECT_ROOT/data/raw/html" -name "*.html" -not -name "_*.html" | wc -l | tr -d ' ')

# Count images
IMAGES=$(find "$PROJECT_ROOT/data/raw/images" -name "*" -type f | wc -l | tr -d ' ')

# Calculate percentage
if [ "$TOTAL_URLS" -gt 0 ]; then
    PERCENTAGE=$(( SCRAPED * 100 / TOTAL_URLS ))
else
    PERCENTAGE=0
fi

echo "Total URLs to scrape: $TOTAL_URLS"
echo "HTML files scraped: $SCRAPED ($PERCENTAGE%)"
echo "Images downloaded: $IMAGES"
echo ""

# Check if scraper is running
if pgrep -f "src.scraper.main" > /dev/null; then
    echo "Status: Scraper is RUNNING"
    
    # Estimate time remaining (assuming 1 second per URL + processing time)
    REMAINING=$((TOTAL_URLS - SCRAPED))
    EST_SECONDS=$((REMAINING * 2))  # 2 seconds per URL to be conservative
    EST_MINUTES=$((EST_SECONDS / 60))
    
    echo "Estimated time remaining: ~$EST_MINUTES minutes"
else
    echo "Status: Scraper is NOT RUNNING"
fi

echo ""

# Show recent files
echo "Recent files scraped:"
ls -lt "$PROJECT_ROOT/data/raw/html" | grep -v "^total" | grep ".html" | head -5

# Check for errors in summary
if [ -f "$PROJECT_ROOT/data/raw/scrape_summary.json" ]; then
    echo ""
    echo "Summary from last run:"
    jq '.' "$PROJECT_ROOT/data/raw/scrape_summary.json" 2>/dev/null || echo "Could not read summary"
fi