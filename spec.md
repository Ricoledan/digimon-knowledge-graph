# Digimon Knowledge Graph Project Specification

**Version**: 1.0  
**Last Updated**: November 2024  
**Status**: Planning Phase

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technical Architecture](#technical-architecture)
3. [Data Model](#data-model)
4. [Pipeline Phases](#pipeline-phases)
5. [Implementation Details](#implementation-details)
6. [Analysis & Deliverables](#analysis--deliverables)
7. [Project Timeline](#project-timeline)

## Project Overview

### Goal
Build a comprehensive knowledge graph from digimon.net/reference to analyze relationships between Digimon based on their characteristics, evolution patterns, and shared attributes.

### Objectives
- Scrape and structure data from Japanese Digimon reference site
- Create a graph database representing Digimon relationships
- Perform network analysis to discover insights
- Publish findings in a technical article

### Scope
- **Data Source**: https://digimon.net/reference/
- **Coverage**: All Digimon detail pages
- **Language**: Japanese source requiring translation
- **Relationships**: Evolution chains, type/attribute connections, shared moves

## Technical Architecture

### Technology Stack
```yaml
Web Scraping:
  - BeautifulSoup4
  - requests
  - asyncio (for concurrent fetching)

Translation:
  - googletrans (primary)
  - deep-translator (fallback)

Data Processing:
  - pandas
  - SpaCy (optional for NLP)

Graph Database:
  - Neo4j Community Edition
  - py2neo (Python driver)

Analysis:
  - NetworkX
  - matplotlib/seaborn
  - Gephi (for advanced visualization)
```

### Project Structure
```
digimon-knowledge-graph/
├── README.md
├── requirements.txt
├── config.yaml
├── src/
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── fetcher.py
│   │   ├── parser.py
│   │   └── translator.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   ├── loader.py
│   │   └── relationships.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   └── visualizations.py
│   └── utils/
│       ├── __init__.py
│       └── cache.py
├── data/
│   ├── raw/
│   │   ├── html/
│   │   ├── images/
│   │   └── index.json
│   ├── processed/
│   │   └── digimon/
│   ├── translations/
│   └── cache/
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── 02_analysis.ipynb
│   └── 03_visualization.ipynb
├── tests/
└── docs/
```

## Data Model

### Source Data Structure
Each Digimon page contains:
- 名前 (Name)
- レベル (Level)
- タイプ (Type)
- 属性 (Attribute)
- 必殺技 (Special Moves)
- プロフィール (Profile)
- 進化 (Evolution) - shows pre-evolution
- キャラクター画像 (Character Image)

### Extracted Schema
```json
{
  "name": "Agumon",
  "japanese_name": "アグモン",
  "level": "Rookie",
  "level_jp": "成長期",
  "type": "Reptile",
  "type_jp": "爬虫類型",
  "attribute": "Vaccine",
  "attribute_jp": "ワクチン",
  "special_moves": [
    {
      "name": "Pepper Breath",
      "japanese_name": "ベビーフレイム"
    }
  ],
  "profile": "A small dinosaur-type Digimon...",
  "profile_jp": "小型の恐竜型デジモン...",
  "evolves_from": "Koromon",
  "image_url": "https://...",
  "source_url": "https://...",
  "scraped_at": "2024-11-20T10:00:00Z"
}
```

### Neo4j Graph Schema

#### Node Types
```cypher
// Primary Entity
(:Digimon {
    name: String,           // English name
    japanese_name: String,  // Original Japanese
    profile: String,        // Translated profile
    profile_jp: String,     // Original profile
    image_url: String,
    source_url: String,
    scraped_at: DateTime
})

// Category Nodes
(:Type {
    name: String,          // e.g., "Dragon", "Machine"
    name_jp: String
})

(:Attribute {
    name: String,          // "Vaccine", "Virus", "Data", "Free"
    name_jp: String
})

(:Level {
    name: String,          // "Rookie", "Champion", etc.
    name_jp: String,
    stage: Integer         // 1-6 for ordering
})

(:Move {
    name: String,
    japanese_name: String
})
```

#### Relationship Types
```cypher
// Direct Relationships (from source data)
(:Digimon)-[:EVOLVES_FROM]->(:Digimon)
(:Digimon)-[:HAS_TYPE]->(:Type)
(:Digimon)-[:HAS_ATTRIBUTE]->(:Attribute)
(:Digimon)-[:HAS_LEVEL]->(:Level)
(:Digimon)-[:CAN_USE]->(:Move)

// Inferred Relationships (computed)
(:Digimon)-[:SHARES_TYPE {weight: Float}]->(:Digimon)
(:Digimon)-[:SHARES_ATTRIBUTE {weight: Float}]->(:Digimon)
(:Digimon)-[:SHARES_LEVEL]->(:Digimon)
(:Digimon)-[:SHARES_MOVE {move_name: String}]->(:Digimon)

// Evolution Chain (computed)
(:Digimon)-[:EVOLUTION_CHAIN {distance: Integer}]->(:Digimon)
```

## Pipeline Phases

### Phase 1: Data Acquisition
**Objective**: Scrape all Digimon pages from source

**Steps**:
1. Fetch index page
2. Extract all detail page URLs
3. Implement polite scraping:
   - Rate limiting (1 request/second)
   - Retry logic for failures
   - Progress tracking
4. Store raw HTML locally

**Output**:
- `data/raw/html/{digimon_id}.html`
- `data/raw/images/{digimon_name}.png` (or .jpg)
- `data/raw/index.json` (URL mapping)
- `data/raw/scrape_log.json`

### Phase 2: Data Extraction & Translation
**Objective**: Parse HTML and translate to English

**Investigation Tasks**:
1. **Element Analysis** - Determine what each HTML element contains:
   - Check `c-titleSet__sub` element - might contain English names
   - Map all relevant CSS classes to data fields
   - Document any inconsistencies across pages
   - Create element-to-field mapping guide

2. **Name Extraction Strategy**:
   ```python
   def extract_digimon_name(soup, url):
       """
       Multi-strategy approach for name extraction
       Priority order:
       1. Check c-titleSet__sub for English name
       2. Extract from URL (directory_name parameter)
       3. Use main title + translation
       4. Fallback to name mapping table
       """
       strategies = {
           'subtitle_element': lambda: soup.find(class_='c-titleSet__sub'),
           'url_parameter': lambda: parse_url_name(url),
           'main_title': lambda: soup.find(class_='c-titleSet__main'),
           'mapping_table': lambda: lookup_official_name(japanese_name)
       }
       # Implementation after investigation
   ```

3. **Data Field Mapping**:
   ```python
   # Investigate and document CSS selectors
   ELEMENT_MAPPING = {
       'name': ['.c-titleSet__main', '.c-titleSet__sub'],
       'level': ['.level-class-tbd'],  # To be determined
       'type': ['.type-class-tbd'],
       'attribute': ['.attribute-class-tbd'],
       'moves': ['.moves-class-tbd'],
       'profile': ['.profile-class-tbd'],
       'evolution': ['.evolution-class-tbd'],
       'image': ['img.digimon-image-class-tbd']
   }
   ```

**Steps**:
1. Parse HTML structure for each page
2. Extract structured fields
3. Implement translation strategy:
   - Cache all translations
   - Batch translate for efficiency
   - Handle official English names
4. Validate data quality

**Translation Priorities**:
1. Names (use official English where available)
2. Categories (Level, Type, Attribute)
3. Special moves
4. Profiles (can be done async)

**Output**:
- `data/processed/digimon/{name}.json`
- `data/translations/cache.json`
- `data/processed/validation_report.json`

### Phase 3: Graph Construction
**Objective**: Build Neo4j knowledge graph

**Steps**:
1. Initialize Neo4j with constraints:
   ```cypher
   CREATE CONSTRAINT unique_digimon_name
   ON (d:Digimon) ASSERT d.name IS UNIQUE;
   
   CREATE INDEX digimon_level
   FOR (d:Digimon) ON (d.level);
   ```

2. Load nodes in order:
   - Category nodes (Type, Attribute, Level, Move)
   - Digimon nodes
   
3. Create relationships:
   - Direct relationships from data
   - Compute inferred relationships

4. Optimize with batch operations

**Output**:
- Populated Neo4j database
- `data/graph/load_stats.json`
- `data/graph/relationship_counts.csv`

### Phase 4: Analysis & Insights
**Objective**: Extract meaningful insights from graph

**Key Analyses**:
1. **Evolution Analysis**
   - Complete evolution chains
   - Most common evolution paths
   - Evolution tree visualization
   
2. **Type/Attribute Distribution**
   - Frequency analysis
   - Common combinations
   - Rare combinations

3. **Network Metrics**
   - Degree centrality (most connected)
   - Community detection
   - Clustering coefficient

4. **Special Moves Analysis**
   - Move sharing patterns
   - Unique vs. common moves
   - Move inheritance through evolution

**Queries Examples**:
```cypher
// Find longest evolution chains
MATCH path = (d1:Digimon)-[:EVOLVES_FROM*]->(d2:Digimon)
WHERE NOT (d1)<-[:EVOLVES_FROM]-()
RETURN path, length(path) as chain_length
ORDER BY chain_length DESC
LIMIT 10;

// Most connected Digimon by shared attributes
MATCH (d:Digimon)-[r:SHARES_TYPE|SHARES_ATTRIBUTE]-(other)
RETURN d.name, COUNT(DISTINCT other) as connections
ORDER BY connections DESC
LIMIT 20;
```

## Implementation Details

### HTML Structure Investigation
```python
def investigate_page_structure(sample_urls):
    """
    Analyze HTML structure to create reliable selectors
    """
    structure_report = {
        'consistent_elements': [],
        'variable_elements': [],
        'data_locations': {}
    }
    
    for url in sample_urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check common patterns
        investigations = {
            'english_in_subtitle': check_element_content('.c-titleSet__sub', 'isascii'),
            'url_name_reliable': verify_url_name_matches(url, soup),
            'image_selector': find_image_elements(soup),
            'data_tables': find_data_containers(soup),
            'evolution_section': locate_evolution_info(soup)
        }
        
    return structure_report

# Key investigations needed:
# 1. Does c-titleSet__sub consistently contain English names?
# 2. Are URL directory_names reliable English translations?
# 3. What's the consistent selector for each data field?
# 4. How is evolution data structured in the HTML?
```

### File Naming Strategy
```python
import re
import unicodedata

def sanitize_filename(name, max_length=255):
    """
    Create safe filenames from Digimon names (handles Japanese + special chars)
    """
    # Option 1: Use romanized names (preferred)
    # Transliterate Japanese to romaji if needed
    
    # Option 2: Use UUID-based naming with lookup table
    # filename = f"{uuid4()}.html"
    
    # Option 3: Sanitize with strict rules
    # Remove/replace illegal characters for Windows/Unix
    illegal_chars = '<>:"/\\|?*'
    control_chars = ''.join(chr(i) for i in range(32))
    
    # Replace illegal characters
    for char in illegal_chars + control_chars:
        name = name.replace(char, '_')
    
    # Handle Unicode normalization
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces and other problematic characters
    name = re.sub(r'[^\w\-_.]', '_', name)
    name = re.sub(r'_{2,}', '_', name)  # Remove multiple underscores
    name = name.strip('_.- ')  # Remove leading/trailing special chars
    
    # Ensure non-empty
    if not name:
        name = 'unnamed'
    
    # Truncate if too long (leave room for extension)
    if len(name) > max_length - 10:
        name = name[:max_length - 10]
    
    return name.lower()

# Recommended approach: ID-based with lookup table
def create_file_structure():
    """
    Use consistent IDs with a lookup table
    """
    file_mapping = {
        "agumon": {
            "id": "digimon_001",
            "japanese_name": "アグモン",
            "html_file": "data/raw/html/digimon_001.html",
            "image_file": "data/raw/images/digimon_001.png",
            "json_file": "data/processed/digimon_001.json"
        }
    }
    
    # Save mapping for reference
    with open('data/file_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(file_mapping, f, ensure_ascii=False, indent=2)
```

### Cross-Platform Considerations
- **Windows**: Max path length 260 chars, no CON, PRN, AUX, etc.
- **Reserved names**: Avoid Windows reserved (NUL, COM1-9, LPT1-9)
- **Case sensitivity**: Use lowercase for consistency
- **Special characters**: Avoid all OS-specific special chars

### Translation Approach
```python
# Translation caching strategy
def get_translation(text, lang='ja'):
    cache_key = f"{lang}:{text}"
    if cache_key in translation_cache:
        return translation_cache[cache_key]
    
    translated = translator.translate(text)
    translation_cache[cache_key] = translated
    
    # Save cache periodically
    if len(translation_cache) % 100 == 0:
        save_cache()
    
    return translated
```

### Relationship Weight Calculation
```python
# Weight formula for shared attribute relationships
def calculate_relationship_weight(attribute, total_with_attribute):
    """
    Inverse frequency weighting:
    Rarer shared attributes = stronger relationship
    """
    if total_with_attribute <= 1:
        return 0
    return 1.0 / math.log(total_with_attribute)
```

## Analysis & Deliverables

### Expected Insights
1. Evolution tree completeness and gaps
2. Type/Attribute clustering patterns
3. Most influential Digimon (network centrality)
4. Rare vs. common characteristics
5. Move inheritance patterns

### Visualizations
1. Interactive evolution tree (D3.js)
2. Type/Attribute heatmap
3. Network graph with communities
4. Statistical distributions
5. Evolution path Sankey diagram

### Final Deliverables
1. **Neo4j Database**
   - Complete graph with all relationships
   - Query templates for common questions

2. **Analysis Report**
   - Key findings with visualizations
   - Statistical summary
   - Interesting discoveries

3. **Technical Article**
   - Process walkthrough
   - Challenges and solutions
   - Code highlights
   - Insights and visualizations

4. **Open Source Release**
   - Clean, documented code
   - Setup instructions
   - Example queries
   - Jupyter notebooks

## Project Timeline

### Week 1: Setup & Scraping
- Environment setup
- Implement scraper
- Complete data acquisition

### Week 2: Processing & Translation
- Parse all pages
- Translate content
- Data validation

### Week 3: Graph Construction
- Neo4j setup
- Data loading
- Relationship creation

### Week 4: Analysis & Writing
- Run analyses
- Create visualizations
- Write article
- Prepare repository

## Success Metrics
- **Coverage**: >95% of Digimon successfully scraped
- **Data Quality**: <1% missing required fields
- **Translation**: 100% of names and categories translated
- **Graph Completeness**: All relationships mapped
- **Performance**: Full pipeline < 3 hours
- **Insights**: Minimum 5 significant findings

## Future Enhancements (v2.0)
- [ ] Image analysis for visual similarity
  - Color palette extraction
  - Shape/silhouette matching
  - Design element detection (wings, armor, etc.)
- [ ] Integrate anime/manga appearance data
- [ ] Add competitive battle statistics
- [ ] Build API for graph queries
- [ ] Create web visualization dashboard
- [ ] Multi-language support

## Image Storage & Analysis (v1.5)

### Image Storage Strategy
- Store all character images during initial scrape
- Maintain original filenames with sanitization
- Create image metadata JSON:
  ```json
  {
    "digimon_name": "Agumon",
    "file_path": "data/raw/images/agumon.png",
    "file_size": 145632,
    "dimensions": {"width": 320, "height": 320},
    "format": "PNG",
    "has_transparency": true
  }
  ```

### Potential Image Analyses
1. **Color Analysis**
   - Dominant color extraction
   - Color palette comparison
   - Type correlation with colors

2. **Visual Similarity Network**
   - Perceptual hashing
   - Feature extraction with CNN
   - Clustering by visual traits

3. **Design Element Detection**
   - Wings/armor/weapons detection
   - Body type classification
   - Evolution visual progression

## Notes & Considerations
- Respect robots.txt and rate limits
- Handle Japanese text encoding properly
- Cache aggressively to avoid re-translation
- Design for incremental updates
- Consider graph size for query performance

---

**Next Steps**: Begin with environment setup and scraper implementation according to Phase 1 specifications.
