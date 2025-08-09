#!/usr/bin/env python3
"""Check status of the Digimon Knowledge Graph pipeline."""

import os
import json
from pathlib import Path
from datetime import datetime

print("DIGIMON KNOWLEDGE GRAPH - PIPELINE STATUS")
print("=" * 60)

# Check environment
print("\nENVIRONMENT:")
print(f"  Working directory: {os.getcwd()}")
print(f"  Python executable: {os.sys.executable}")

# Check data directories
dirs_to_check = {
    "Raw HTML": "data/raw/html",
    "Raw Images": "data/raw/images", 
    "Processed JSON": "data/processed/digimon",
    "Translated": "data/translated",
    "Cache": "data/cache"
}

print("\nDATA DIRECTORIES:")
for name, path in dirs_to_check.items():
    p = Path(path)
    if p.exists():
        files = list(p.glob("*.*"))
        files = [f for f in files if not f.name.startswith("_")]
        print(f"  {name}: [OK] {len(files)} files")
    else:
        print(f"  {name}: [MISSING] Not found")

# Check URLs file
print("\nDIGIMON URLS:")
urls_file = Path("data/raw/html/_all_digimon_urls.json")
if urls_file.exists():
    with open(urls_file) as f:
        data = json.load(f)
        print(f"  Total URLs: [OK] {data['total_urls']} Digimon found")
else:
    print("  URLs file: [MISSING] Not found")

# Check scraped data
print("\nSCRAPED DATA:")
html_files = list(Path("data/raw/html").glob("*.html"))
html_files = [f for f in html_files if not f.name.startswith("_")]
print(f"  HTML files: {len(html_files)} scraped")

# Check parsed data
print("\nPARSED DATA:")
json_files = list(Path("data/processed/digimon").glob("*.json"))
json_files = [f for f in json_files if not f.name.startswith("_")]
print(f"  JSON files: {len(json_files)} parsed")

# Check translated data
print("\nTRANSLATED DATA:")
trans_dir = Path("data/translated")
if trans_dir.exists():
    trans_files = list(trans_dir.glob("*.json"))
    trans_files = [f for f in trans_files if not f.name.startswith("_")]
    print(f"  Translated files: {len(trans_files)}")
    
    # Check test translations
    test_dir = trans_dir / "test"
    if test_dir.exists():
        test_files = list(test_dir.glob("*.json"))
        print(f"  Test translations: {len(test_files)}")

# Check cache
print("\nTRANSLATION CACHE:")
cache_file = Path("data/cache/translations.json")
if cache_file.exists():
    with open(cache_file) as f:
        cache = json.load(f)
        print(f"  Cached translations: {len(cache)}")
else:
    print("  Cache: Not found")

# Pipeline status
print("\nPIPELINE STATUS:")
steps = [
    ("1. URL Discovery", len(html_files) > 0 or urls_file.exists()),
    ("2. HTML Scraping", len(html_files) > 0),
    ("3. Data Parsing", len(json_files) > 0),
    ("4. Translation", (Path("data/translated/test").exists() and 
                       len(list(Path("data/translated/test").glob("*.json"))) > 0)),
    ("5. Neo4j Loading", Path("src/graph/loader.py").exists())
]

for step, completed in steps:
    status = "[READY]" if completed else "[PENDING]"
    print(f"  {step}: {status}")

# Next steps
print("\nNEXT STEPS:")
if len(html_files) < 100:  # Assuming we want all 1,249
    print("  1. Run full scraper: python -m src.scraper.main --fetch-api-first")
elif len(json_files) < len(html_files):
    print("  1. Parse HTML files: python -m src.parser.main")
elif not Path("data/translated").exists() or len(list(Path("data/translated").glob("*.json"))) < len(json_files):
    print("  1. Translate data: python -m src.processor.main")
else:
    print("  1. Start Neo4j: ./scripts/database/start_neo4j.sh")
    print("  2. Load into Neo4j: python -m src.graph.loader")
    print("  3. Run analysis: python -m src.analysis.main")

print("\n" + "=" * 60)