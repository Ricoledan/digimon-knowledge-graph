#!/usr/bin/env bash
# Run the HTML parser to extract structured data

set -e

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

echo "========================================"
echo "Digimon HTML Parser"
echo "========================================"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if we have HTML files to parse
HTML_COUNT=$(find data/raw/html -name "*.html" -not -name "_*.html" 2>/dev/null | wc -l | tr -d ' ')

if [ "$HTML_COUNT" -eq 0 ]; then
    echo "Error: No HTML files found in data/raw/html/"
    echo "Please run the scraper first: ./scripts/scraping/run_scraper.sh"
    exit 1
fi

echo "Found $HTML_COUNT HTML files to parse"
echo ""

# Run the parser
echo "Starting parser..."
python -m src.parser.main

echo ""

# Show results
if [ -f "data/processed/digimon/_parsing_summary.json" ]; then
    echo "Parsing Summary:"
    jq '.' "data/processed/digimon/_parsing_summary.json"
fi

# Count output files
JSON_COUNT=$(find data/processed/digimon -name "*.json" -not -name "_*.json" 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "Created $JSON_COUNT JSON files"
echo ""
echo "Next steps:"
echo "1. Translate Japanese content: ./scripts/translation/run_translator.sh"
echo "2. Load into Neo4j: ./scripts/database/load_to_neo4j.sh"