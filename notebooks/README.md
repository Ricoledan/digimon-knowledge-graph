# Digimon Knowledge Graph Analysis Notebooks

This directory contains Jupyter notebooks for analyzing the Digimon Knowledge Graph data.

## Setup

### Installing Dependencies

Before running the notebooks, install all required dependencies:

```bash
# From the notebooks directory
pip install -r requirements.txt
```

### Required Packages

The notebooks require the following packages:
- **pandas**: Data manipulation and analysis
- **matplotlib/seaborn**: Data visualization
- **plotly**: Interactive visualizations
- **networkx**: Graph analysis
- **scikit-learn**: Machine learning algorithms for clustering
- **python-louvain**: Community detection algorithms
- **pyvis**: Interactive network visualization

## Notebooks Overview

1. **01_data_exploration.ipynb**: Initial data exploration and profiling
   - Database connection verification
   - Basic statistics and distributions
   - Data quality assessment
   - Type, attribute, and level distributions

2. **02_evolution_analysis.ipynb**: Evolution network analysis
   - Evolution chains and pathways
   - Type transitions through evolution
   - Branching patterns and complexity
   - Evolution network visualization

3. **03_type_attribute_correlation.ipynb**: Statistical correlation analysis
   - Type-attribute associations
   - Chi-square tests and Cramér's V
   - Pattern mining with association rules
   - Predictive analysis of attributes

4. **04_move_network_analysis.ipynb**: Special move analysis
   - Move frequency and diversity
   - Move-based clustering
   - Move inheritance through evolution
   - Co-occurrence network analysis

5. **05_community_detection.ipynb**: Graph clustering and communities
   - Louvain community detection
   - Label propagation algorithms
   - Community characteristics
   - Inter-community relationships

6. **06_centrality_analysis.ipynb**: Network centrality measures
   - Degree, betweenness, closeness centrality
   - PageRank and eigenvector centrality
   - Hub and authority scores
   - Most influential Digimon

7. **07_predictive_modeling.ipynb**: Machine learning models
   - Type and attribute prediction
   - Evolution prediction
   - Feature importance analysis
   - Model performance evaluation

8. **08_recommendation_system.ipynb**: Similarity and recommendations
   - Digimon similarity metrics
   - Content-based recommendations
   - Team composition suggestions
   - Evolution path recommendations

## Running the Notebooks

1. Ensure Neo4j is running:
   ```bash
   ygg start
   ```

2. Install notebook dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start Jupyter:
   ```bash
   jupyter notebook
   ```

4. Run notebooks in order (01 → 08) for best results

## Troubleshooting

If you encounter import errors:
1. Ensure you've installed all dependencies: `pip install -r requirements.txt`
2. Check that you're in the correct Python environment
3. Verify Neo4j is running: `ygg db-status`

## Output

Each notebook saves results to its own organized directory:
- `results/{notebook_name}/data/`: Data exports and statistics
- `results/{notebook_name}/figures/`: Generated visualizations

For example:
- `results/01_data_exploration/data/`: Graph statistics, distributions
- `results/02_evolution_analysis/figures/`: Evolution network diagrams
- `results/07_predictive_modeling/models/`: Trained ML models