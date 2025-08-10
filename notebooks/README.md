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

2. **02_network_analysis.ipynb**: Graph structure and metrics
   - Centrality measures
   - Network topology analysis
   - Path and connectivity analysis

3. **03_community_detection.ipynb**: Community and clustering analysis
   - Community detection algorithms
   - Cluster validation
   - Evolution pattern analysis

4. **04_evolution_patterns.ipynb**: Evolution chain analysis
   - Evolution pathways
   - Type transitions
   - Level progression patterns

5. **05_visualization_dashboard.ipynb**: Interactive visualizations
   - Network visualizations
   - Interactive dashboards
   - Export-ready figures

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

4. Run notebooks in order (01 → 05) for best results

## Troubleshooting

If you encounter import errors:
1. Ensure you've installed all dependencies: `pip install -r requirements.txt`
2. Check that you're in the correct Python environment
3. Verify Neo4j is running: `ygg db-status`

## Output

Results are saved to the `results/` directory:
- `results/data/`: Data exports and statistics
- `results/figures/`: Generated visualizations
- `results/analysis/`: Analysis reports and findings