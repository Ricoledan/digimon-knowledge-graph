"""
Visualization utilities for Digimon Knowledge Graph analysis.
Provides consistent styling and reusable plot functions.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from pyvis.network import Network
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import yaml

# Load configuration
config_path = Path(__file__).parent.parent / "config" / "analysis_config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Set visualization defaults
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette(config['analysis']['visualization']['color_palette'])
plt.rcParams['figure.figsize'] = config['analysis']['visualization']['figure_size']
plt.rcParams['figure.dpi'] = config['analysis']['visualization']['figure_dpi']

# Digimon type colors
TYPE_COLORS = {
    'Dragon': '#FF6B6B',
    'Beast': '#8B4513',
    'Machine': '#708090',
    'Insect': '#228B22',
    'Bird': '#87CEEB',
    'Aquan': '#4682B4',
    'Holy': '#FFD700',
    'Dark': '#4B0082',
    'Plant': '#32CD32',
    'Warrior': '#DC143C',
    'Fairy': '#FF69B4',
    'Demon': '#8B008B',
    'Undead': '#2F4F4F',
    'Rock': '#A0522D',
    'Fire': '#FF4500',
    'Ice': '#00CED1',
    'Electric': '#FFFF00',
    'Other': '#808080'
}

# Attribute colors
ATTRIBUTE_COLORS = {
    'Vaccine': '#00FF00',
    'Virus': '#FF0000',
    'Data': '#0000FF',
    'Free': '#FFFF00',
    'Unknown': '#808080'
}

# Level colors
LEVEL_COLORS = {
    'Baby': '#FFE5CC',
    'In-Training': '#FFD4B3',
    'Rookie': '#FFC299',
    'Champion': '#FFB380',
    'Ultimate': '#FF9966',
    'Mega': '#FF8C42',
    'Ultra': '#FF6B1A',
    'Unknown': '#808080'
}


def save_figure(fig, filename: str, formats: Optional[List[str]] = None):
    """Save figure in multiple formats."""
    if formats is None:
        formats = config['export']['figure_formats']
    
    figures_dir = Path(config['paths']['figures_dir'])
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    for fmt in formats:
        filepath = figures_dir / f"{filename}.{fmt}"
        if hasattr(fig, 'savefig'):  # Matplotlib
            fig.savefig(filepath, bbox_inches='tight', dpi=300)
        elif hasattr(fig, 'write_html'):  # Plotly
            if fmt == 'html':
                fig.write_html(str(filepath))
            elif fmt == 'png':
                fig.write_image(str(filepath))
        print(f"Saved: {filepath}")


def plot_distribution(data: pd.Series, title: str, xlabel: str, ylabel: str = "Count",
                     color_map: Optional[Dict[str, str]] = None, top_n: Optional[int] = None):
    """Create a bar plot for categorical distributions."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Prepare data
    counts = data.value_counts()
    if top_n:
        counts = counts.head(top_n)
    
    # Colors
    if color_map:
        colors = [color_map.get(x, '#808080') for x in counts.index]
    else:
        colors = sns.color_palette('husl', len(counts))
    
    # Create bar plot
    bars = ax.bar(range(len(counts)), counts.values, color=colors)
    
    # Customize
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(counts.index, rotation=45, ha='right')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=16, fontweight='bold')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    return fig


def plot_heatmap(data: pd.DataFrame, title: str, cmap: str = 'YlOrRd',
                 figsize: Tuple[int, int] = (10, 8), annot: bool = True):
    """Create a heatmap visualization."""
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.heatmap(data, annot=annot, fmt='d' if annot else '.2f',
                cmap=cmap, cbar_kws={'label': 'Count'},
                ax=ax, square=True)
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    return fig


def plot_network_interactive(G: nx.Graph, title: str = "Digimon Network",
                           node_color_attr: Optional[str] = None,
                           node_size_attr: Optional[str] = None,
                           layout: str = 'spring'):
    """Create interactive network visualization using pyvis."""
    net = Network(height="750px", width="100%", bgcolor="#222222", 
                  font_color="white", notebook=True)
    
    # Set physics options
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true,
        "stabilization": {
          "enabled": true,
          "iterations": 100
        }
      }
    }
    """)
    
    # Add nodes
    for node in G.nodes():
        node_attrs = G.nodes[node]
        
        # Determine color
        if node_color_attr and node_color_attr in node_attrs:
            value = node_attrs[node_color_attr]
            if node_color_attr == 'type':
                color = TYPE_COLORS.get(value, '#808080')
            elif node_color_attr == 'attribute':
                color = ATTRIBUTE_COLORS.get(value, '#808080')
            elif node_color_attr == 'level':
                color = LEVEL_COLORS.get(value, '#808080')
            else:
                color = '#808080'
        else:
            color = '#97C2FC'
        
        # Determine size
        if node_size_attr and node_size_attr in node_attrs:
            size = 10 + node_attrs[node_size_attr] * 2
        else:
            size = 20
        
        # Add node
        net.add_node(node, 
                    label=str(node),
                    color=color,
                    size=size,
                    title=f"{node}<br>" + "<br>".join([f"{k}: {v}" for k, v in node_attrs.items()]))
    
    # Add edges
    for edge in G.edges():
        net.add_edge(edge[0], edge[1])
    
    # Generate HTML
    net.show_buttons(filter_=['physics'])
    return net


def plot_network_static(G: nx.Graph, title: str = "Digimon Network",
                       node_color_attr: Optional[str] = None,
                       node_size_attr: Optional[str] = None,
                       layout: str = 'spring',
                       figsize: Tuple[int, int] = (15, 15)):
    """Create static network visualization using matplotlib."""
    fig, ax = plt.subplots(figsize=figsize)
    
    # Choose layout
    if layout == 'spring':
        pos = nx.spring_layout(G, k=1/np.sqrt(len(G.nodes())), iterations=50)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    else:
        pos = nx.spring_layout(G)
    
    # Prepare node colors
    if node_color_attr:
        node_colors = []
        for node in G.nodes():
            value = G.nodes[node].get(node_color_attr, 'Unknown')
            if node_color_attr == 'type':
                color = TYPE_COLORS.get(value, '#808080')
            elif node_color_attr == 'attribute':
                color = ATTRIBUTE_COLORS.get(value, '#808080')
            elif node_color_attr == 'level':
                color = LEVEL_COLORS.get(value, '#808080')
            else:
                color = '#808080'
            node_colors.append(color)
    else:
        node_colors = '#97C2FC'
    
    # Prepare node sizes
    if node_size_attr:
        node_sizes = [300 + G.nodes[node].get(node_size_attr, 0) * 50 for node in G.nodes()]
    else:
        node_sizes = 300
    
    # Draw network
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                          alpha=0.8, ax=ax)
    nx.draw_networkx_edges(G, pos, alpha=0.3, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, ax=ax)
    
    ax.set_title(title, fontsize=20, fontweight='bold')
    ax.axis('off')
    plt.tight_layout()
    return fig


def plot_evolution_sankey(evolution_data: List[Dict[str, str]], title: str = "Evolution Flow"):
    """Create Sankey diagram for evolution paths."""
    # Prepare data for Sankey
    sources = []
    targets = []
    values = []
    labels = []
    
    # Count transitions
    transitions = {}
    for evo in evolution_data:
        key = (evo['from_digimon'], evo['to_digimon'])
        transitions[key] = transitions.get(key, 0) + 1
    
    # Build label list
    all_digimon = set()
    for (source, target) in transitions.keys():
        all_digimon.add(source)
        all_digimon.add(target)
    labels = list(all_digimon)
    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    
    # Build source, target, value lists
    for (source, target), count in transitions.items():
        sources.append(label_to_idx[source])
        targets.append(label_to_idx[target])
        values.append(count)
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values
        )
    )])
    
    fig.update_layout(title_text=title, font_size=10, height=800)
    return fig


def plot_centrality_comparison(centrality_scores: pd.DataFrame, 
                              title: str = "Centrality Measures Comparison",
                              top_n: int = 20):
    """Create radar chart comparing different centrality measures."""
    # Get top N by average centrality
    centrality_scores['avg_centrality'] = centrality_scores.mean(axis=1)
    top_nodes = centrality_scores.nlargest(top_n, 'avg_centrality')
    
    # Normalize scores to 0-1 range
    normalized = top_nodes.drop('avg_centrality', axis=1)
    normalized = (normalized - normalized.min()) / (normalized.max() - normalized.min())
    
    # Create subplot for each node
    fig = make_subplots(
        rows=4, cols=5,
        subplot_titles=normalized.index[:20],
        specs=[[{'type': 'polar'}] * 5] * 4
    )
    
    measures = normalized.columns.tolist()
    
    for idx, (node, scores) in enumerate(normalized.iterrows()):
        row = idx // 5 + 1
        col = idx % 5 + 1
        
        fig.add_trace(
            go.Scatterpolar(
                r=scores.values.tolist() + [scores.values[0]],
                theta=measures + [measures[0]],
                fill='toself',
                name=node
            ),
            row=row, col=col
        )
    
    fig.update_layout(
        showlegend=False,
        title_text=title,
        height=1200
    )
    
    return fig


def plot_community_network(G: nx.Graph, communities: Dict[int, List[str]], 
                          title: str = "Community Structure"):
    """Visualize network with community coloring."""
    # Create color map for communities
    node_to_community = {}
    for comm_id, nodes in communities.items():
        for node in nodes:
            node_to_community[node] = comm_id
    
    # Generate colors
    num_communities = len(communities)
    colors = plt.cm.rainbow(np.linspace(0, 1, num_communities))
    
    node_colors = []
    for node in G.nodes():
        comm_id = node_to_community.get(node, -1)
        if comm_id >= 0:
            node_colors.append(colors[comm_id])
        else:
            node_colors.append('#808080')
    
    return plot_network_static(G, title=title, node_color_attr=None,
                              figsize=(15, 15))


def create_dashboard(stats: Dict[str, Any], title: str = "Digimon Knowledge Graph Dashboard"):
    """Create comprehensive dashboard with multiple visualizations."""
    fig = make_subplots(
        rows=3, cols=3,
        subplot_titles=('Node Distribution', 'Relationship Distribution', 'Level Distribution',
                       'Type Distribution', 'Attribute Distribution', 'Graph Density',
                       'Degree Distribution', 'Connected Components', 'Path Lengths'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'pie'}],
               [{'type': 'bar'}, {'type': 'pie'}, {'type': 'indicator'}],
               [{'type': 'histogram'}, {'type': 'bar'}, {'type': 'box'}]]
    )
    
    # Add traces based on available statistics
    # This is a template - actual implementation would use real data
    
    fig.update_layout(height=1200, showlegend=False, title_text=title)
    return fig