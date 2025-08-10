# Digimon Network Analysis: Visualization Guide

**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Comprehensive visualization specifications and examples for the Digimon Knowledge Graph article

---

## Table of Contents

1. [Visualization Philosophy](#1-visualization-philosophy)
2. [Color Theory & Design System](#2-color-theory--design-system)
3. [Static Visualizations](#3-static-visualizations)
4. [Interactive Visualizations](#4-interactive-visualizations)
5. [Network Visualizations](#5-network-visualizations)
6. [Statistical Visualizations](#6-statistical-visualizations)
7. [Machine Learning Visualizations](#7-machine-learning-visualizations)
8. [Dashboard Specifications](#8-dashboard-specifications)
9. [Publication Guidelines](#9-publication-guidelines)
10. [Implementation Examples](#10-implementation-examples)

---

## 1. Visualization Philosophy

### 1.1 Core Principles

1. **Clarity Over Complexity**
   - Each visualization should communicate one primary insight
   - Remove all non-essential elements
   - Use progressive disclosure for complexity

2. **Consistency is Key**
   - Unified color palette across all visualizations
   - Consistent typography and spacing
   - Standardized interaction patterns

3. **Accessibility First**
   - Color-blind friendly palettes
   - High contrast ratios
   - Alternative text descriptions
   - Keyboard navigation for interactive elements

4. **Story-Driven Design**
   - Each visualization advances the narrative
   - Clear titles that state the insight
   - Annotations highlight key findings

### 1.2 Visual Hierarchy

```
Title (Main Insight)
├── Primary Visual Element
├── Supporting Context
├── Interactive Controls (if applicable)
└── Caption/Interpretation
```

---

## 2. Color Theory & Design System

### 2.1 Primary Color Palette

```python
# Main type colors with semantic meaning
TYPE_COLOR_SYSTEM = {
    # Warm colors for aggressive types
    'Dragon': {
        'primary': '#E53E3E',    # Crimson red
        'light': '#FC8181',
        'dark': '#9B2C2C',
        'accent': '#FEB2B2'
    },
    'Fire': {
        'primary': '#ED8936',    # Flame orange
        'light': '#F6AD55',
        'dark': '#C05621',
        'accent': '#FBD38D'
    },
    
    # Cool colors for defensive types
    'Machine': {
        'primary': '#718096',    # Steel gray
        'light': '#A0AEC0',
        'dark': '#4A5568',
        'accent': '#CBD5E0'
    },
    'Ice': {
        'primary': '#5B9BD5',    # Ice blue
        'light': '#90CDF4',
        'dark': '#2B6CB0',
        'accent': '#BEE3F8'
    },
    
    # Natural colors for organic types
    'Plant': {
        'primary': '#48BB78',    # Forest green
        'light': '#68D391',
        'dark': '#2F855A',
        'accent': '#9AE6B4'
    },
    'Beast': {
        'primary': '#B7791F',    # Earth brown
        'light': '#D69E2E',
        'dark': '#975A16',
        'accent': '#F6E05E'
    }
}

# Attribute colors with game-inspired palette
ATTRIBUTE_COLORS = {
    'Vaccine': '#3182CE',    # Hero blue
    'Virus': '#E53E3E',      # Villain red
    'Data': '#ECC94B',       # Neutral yellow
    'Free': '#718096',       # Variable gray
    'Unknown': '#A0AEC0'     # Light gray
}

# UI/UX colors
UI_COLORS = {
    'background': '#F7FAFC',
    'surface': '#FFFFFF',
    'border': '#E2E8F0',
    'text_primary': '#2D3748',
    'text_secondary': '#718096',
    'interactive': '#4299E1',
    'success': '#48BB78',
    'warning': '#ECC94B',
    'error': '#E53E3E'
}
```

### 2.2 Color Application Rules

1. **Type Colors**: Used for node coloring in networks
2. **Attribute Colors**: Used for categorical comparisons
3. **Gradient Scales**: For continuous values
4. **Semantic Colors**: For UI feedback and states

---

## 3. Static Visualizations

### 3.1 Distribution Charts

**Level Distribution Bar Chart**
```python
def create_level_distribution_chart(data):
    """
    Enhanced bar chart showing Digimon distribution across evolution levels
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Data preparation
    levels = ['Baby', 'In-Training', 'Rookie', 'Champion', 'Ultimate', 'Mega']
    counts = [data[level] for level in levels]
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(levels)))
    
    # Create bars
    bars = ax.bar(levels, counts, color=colors, edgecolor='white', linewidth=2)
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.annotate(f'{count}\n({count/sum(counts)*100:.1f}%)',
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=10, fontweight='bold')
    
    # Styling
    ax.set_title('Distribution of Digimon Across Evolution Levels', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Evolution Level', fontsize=12)
    ax.set_ylabel('Number of Digimon', fontsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Add trend line
    x_pos = range(len(levels))
    z = np.polyfit(x_pos, counts, 2)
    p = np.poly1d(z)
    ax.plot(x_pos, p(x_pos), "r--", alpha=0.6, linewidth=2)
    
    plt.tight_layout()
    return fig
```

**Type Sunburst Chart**
```python
def create_type_sunburst(type_data):
    """
    Hierarchical sunburst showing type categories and subtypes
    """
    import plotly.express as px
    
    # Prepare hierarchical data
    df = pd.DataFrame({
        'category': type_data['category'],
        'type': type_data['type'],
        'count': type_data['count'],
        'path': type_data['category'] + '/' + type_data['type']
    })
    
    fig = px.sunburst(
        df,
        path=['category', 'type'],
        values='count',
        color='count',
        hover_data=['count'],
        color_continuous_scale='Viridis',
        title='Hierarchical Type Distribution of Digimon'
    )
    
    fig.update_layout(
        font=dict(size=14),
        title_font=dict(size=18),
        height=600,
        width=600
    )
    
    return fig
```

### 3.2 Correlation Matrices

**Type-Attribute Correlation Heatmap**
```python
def create_correlation_heatmap(correlation_matrix, significance_matrix):
    """
    Correlation heatmap with significance indicators
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Create mask for non-significant correlations
    mask = significance_matrix > 0.05
    
    # Plot heatmap
    sns.heatmap(correlation_matrix,
                annot=True,
                fmt='.2f',
                cmap='RdBu_r',
                center=0,
                vmin=-1, vmax=1,
                square=True,
                linewidths=0.5,
                cbar_kws={"shrink": 0.8},
                ax=ax)
    
    # Add significance stars
    for i in range(len(correlation_matrix)):
        for j in range(len(correlation_matrix)):
            if significance_matrix[i, j] < 0.001:
                text = '***'
            elif significance_matrix[i, j] < 0.01:
                text = '**'
            elif significance_matrix[i, j] < 0.05:
                text = '*'
            else:
                text = ''
            
            if text:
                ax.text(j + 0.5, i + 0.7, text,
                       ha='center', va='center',
                       color='white', fontsize=12, fontweight='bold')
    
    ax.set_title('Type-Attribute Correlations with Statistical Significance',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Digimon Type', fontsize=12)
    ax.set_ylabel('Digimon Attribute', fontsize=12)
    
    # Add legend for significance
    ax.text(1.02, 0.5, '* p < 0.05\n** p < 0.01\n*** p < 0.001',
            transform=ax.transAxes, fontsize=10,
            verticalalignment='center')
    
    plt.tight_layout()
    return fig
```

---

## 4. Interactive Visualizations

### 4.1 Network Explorer

**Interactive Digimon Network**
```python
def create_interactive_network(G, layout='force'):
    """
    Create interactive network visualization with Pyvis
    """
    from pyvis.network import Network
    
    # Initialize network
    net = Network(height='800px', width='100%', 
                  bgcolor='#F7FAFC', font_color='#2D3748')
    
    # Configure physics
    net.set_options("""
    var options = {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08
            },
            "solver": "forceAtlas2Based",
            "stabilization": {
                "iterations": 150
            }
        },
        "nodes": {
            "shape": "dot",
            "scaling": {
                "min": 10,
                "max": 50
            }
        },
        "edges": {
            "smooth": {
                "type": "continuous"
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
        }
    }
    """)
    
    # Add nodes with properties
    for node in G.nodes():
        node_data = G.nodes[node]
        
        # Size by centrality
        size = 10 + (node_data.get('centrality', 0) * 40)
        
        # Color by type
        color = TYPE_COLOR_SYSTEM.get(
            node_data.get('type', 'Unknown'), 
            {'primary': '#718096'}
        )['primary']
        
        # Hover information
        title = f"""
        <b>{node_data.get('name_en', node)}</b><br>
        Type: {node_data.get('type', 'Unknown')}<br>
        Level: {node_data.get('level', 'Unknown')}<br>
        Attribute: {node_data.get('attribute', 'Unknown')}<br>
        Centrality: {node_data.get('centrality', 0):.3f}
        """
        
        net.add_node(node, 
                     label=node_data.get('name_en', node),
                     title=title,
                     size=size,
                     color=color,
                     borderWidth=2,
                     borderWidthSelected=4)
    
    # Add edges with relationship types
    for edge in G.edges(data=True):
        edge_data = edge[2]
        net.add_edge(edge[0], edge[1],
                     value=edge_data.get('weight', 1),
                     title=edge_data.get('type', 'Related'))
    
    return net
```

### 4.2 Evolution Path Explorer

**Interactive Evolution Tree**
```python
def create_evolution_explorer():
    """
    D3.js-based evolution path explorer
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            .node {
                cursor: pointer;
            }
            .node circle {
                stroke: #fff;
                stroke-width: 2px;
            }
            .link {
                fill: none;
                stroke: #ccc;
                stroke-width: 2px;
            }
            .tooltip {
                position: absolute;
                padding: 10px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                border-radius: 5px;
                pointer-events: none;
                font-size: 12px;
            }
            .search-box {
                position: absolute;
                top: 10px;
                right: 10px;
                padding: 5px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <input type="text" class="search-box" placeholder="Search Digimon...">
        <div id="evolution-tree"></div>
        <script>
            // Evolution tree implementation
            const width = window.innerWidth;
            const height = window.innerHeight;
            
            const svg = d3.select("#evolution-tree")
                .append("svg")
                .attr("width", width)
                .attr("height", height);
                
            const g = svg.append("g");
            
            // Zoom behavior
            const zoom = d3.zoom()
                .scaleExtent([0.1, 10])
                .on("zoom", (event) => {
                    g.attr("transform", event.transform);
                });
                
            svg.call(zoom);
            
            // Load and render evolution data
            d3.json("evolution_data.json").then(function(data) {
                const root = d3.hierarchy(data);
                const treeLayout = d3.tree().size([width - 100, height - 100]);
                
                treeLayout(root);
                
                // Render links
                g.selectAll(".link")
                    .data(root.links())
                    .enter().append("path")
                    .attr("class", "link")
                    .attr("d", d3.linkHorizontal()
                        .x(d => d.y)
                        .y(d => d.x));
                
                // Render nodes
                const node = g.selectAll(".node")
                    .data(root.descendants())
                    .enter().append("g")
                    .attr("class", "node")
                    .attr("transform", d => `translate(${d.y},${d.x})`);
                    
                // Add circles
                node.append("circle")
                    .attr("r", d => 5 + d.data.centrality * 10)
                    .style("fill", d => getTypeColor(d.data.type));
                    
                // Add labels
                node.append("text")
                    .attr("dx", 12)
                    .attr("dy", 4)
                    .text(d => d.data.name)
                    .style("font-size", "10px");
                
                // Add tooltip
                const tooltip = d3.select("body").append("div")
                    .attr("class", "tooltip")
                    .style("opacity", 0);
                    
                node.on("mouseover", function(event, d) {
                    tooltip.transition()
                        .duration(200)
                        .style("opacity", .9);
                    tooltip.html(getTooltipContent(d.data))
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", function(d) {
                    tooltip.transition()
                        .duration(500)
                        .style("opacity", 0);
                });
            });
        </script>
    </body>
    </html>
    """
    
    return html_template
```

---

## 5. Network Visualizations

### 5.1 Community Structure Visualization

**3D Community Network**
```python
def create_3d_community_network(G, communities):
    """
    3D visualization of community structure using Plotly
    """
    import plotly.graph_objects as go
    
    # Compute 3D layout
    pos = nx.spring_layout(G, dim=3, k=1/np.sqrt(len(G)), iterations=50)
    
    # Create traces for each community
    traces = []
    
    for comm_id, community in enumerate(communities):
        # Extract positions
        x_nodes = [pos[node][0] for node in community]
        y_nodes = [pos[node][1] for node in community]
        z_nodes = [pos[node][2] for node in community]
        
        # Node trace
        node_trace = go.Scatter3d(
            x=x_nodes,
            y=y_nodes,
            z=z_nodes,
            mode='markers',
            name=f'Community {comm_id + 1}',
            marker=dict(
                size=[G.degree(node) + 5 for node in community],
                color=f'#{comm_id:02x}{(comm_id*40)%256:02x}{(comm_id*80)%256:02x}',
                line=dict(color='white', width=0.5)
            ),
            text=[f"{G.nodes[node]['name_en']}<br>"
                  f"Type: {G.nodes[node]['type']}<br>"
                  f"Community: {comm_id + 1}"
                  for node in community],
            hoverinfo='text'
        )
        traces.append(node_trace)
    
    # Add edges
    edge_trace = go.Scatter3d(
        x=[],
        y=[],
        z=[],
        mode='lines',
        line=dict(color='rgba(125,125,125,0.2)', width=0.5),
        hoverinfo='none'
    )
    
    for edge in G.edges():
        if edge[0] in pos and edge[1] in pos:
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            edge_trace['x'] += (x0, x1, None)
            edge_trace['y'] += (y0, y1, None)
            edge_trace['z'] += (z0, z1, None)
    
    traces.insert(0, edge_trace)
    
    # Create figure
    fig = go.Figure(data=traces)
    
    fig.update_layout(
        title='3D Community Structure of Digimon Network',
        showlegend=True,
        scene=dict(
            xaxis=dict(showbackground=False),
            yaxis=dict(showbackground=False),
            zaxis=dict(showbackground=False)
        ),
        margin=dict(b=20, l=5, r=5, t=40),
        height=800
    )
    
    return fig
```

### 5.2 Influence Propagation Animation

**Animated Influence Spread**
```python
def create_influence_animation(G, seed_nodes, steps=20):
    """
    Animate influence propagation through the network
    """
    import matplotlib.animation as animation
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Layout
    pos = nx.spring_layout(G, k=2/np.sqrt(len(G)), iterations=50)
    
    # Initialize influence scores
    influence_scores = {node: 0 for node in G.nodes()}
    for seed in seed_nodes:
        influence_scores[seed] = 1.0
    
    def update(frame):
        ax.clear()
        
        # Propagate influence
        new_scores = influence_scores.copy()
        for node in G.nodes():
            if influence_scores[node] > 0:
                for neighbor in G.neighbors(node):
                    # Influence decay
                    transfer = influence_scores[node] * 0.3
                    new_scores[neighbor] = min(1.0, new_scores[neighbor] + transfer)
        
        # Update scores
        for node in G.nodes():
            influence_scores[node] = new_scores[node] * 0.95  # Decay
        
        # Draw network
        node_colors = [influence_scores[node] for node in G.nodes()]
        
        nx.draw_networkx_nodes(G, pos, 
                              node_color=node_colors,
                              node_size=300,
                              cmap='Reds',
                              vmin=0, vmax=1,
                              ax=ax)
        
        nx.draw_networkx_edges(G, pos,
                              alpha=0.2,
                              ax=ax)
        
        # Add labels for influenced nodes
        labels = {node: G.nodes[node]['name_en'] 
                 for node in G.nodes() if influence_scores[node] > 0.1}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)
        
        ax.set_title(f'Influence Propagation - Step {frame}', fontsize=16)
        ax.axis('off')
        
        return ax.artists
    
    anim = animation.FuncAnimation(fig, update, frames=steps, 
                                  interval=500, blit=False)
    
    return anim
```

---

## 6. Statistical Visualizations

### 6.1 Distribution Analysis

**Multi-Panel Statistical Overview**
```python
def create_statistical_dashboard(data):
    """
    Comprehensive statistical visualization dashboard
    """
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Evolution Chain Length Distribution
    ax1 = fig.add_subplot(gs[0, 0])
    chain_lengths = data['evolution_chain_lengths']
    ax1.hist(chain_lengths, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
    ax1.axvline(np.mean(chain_lengths), color='red', linestyle='--', 
                label=f'Mean: {np.mean(chain_lengths):.1f}')
    ax1.set_title('Evolution Chain Length Distribution')
    ax1.set_xlabel('Chain Length')
    ax1.set_ylabel('Frequency')
    ax1.legend()
    
    # 2. Degree Distribution (log-log)
    ax2 = fig.add_subplot(gs[0, 1])
    degrees = data['degree_distribution']
    degree_counts = Counter(degrees)
    x = list(degree_counts.keys())
    y = list(degree_counts.values())
    ax2.loglog(x, y, 'bo-', markersize=8)
    ax2.set_title('Degree Distribution (Log-Log Scale)')
    ax2.set_xlabel('Degree')
    ax2.set_ylabel('Count')
    ax2.grid(True, alpha=0.3)
    
    # 3. Type vs Level Heatmap
    ax3 = fig.add_subplot(gs[0, 2])
    type_level_matrix = data['type_level_matrix']
    sns.heatmap(type_level_matrix, cmap='YlOrRd', annot=True, fmt='d', ax=ax3)
    ax3.set_title('Type Distribution by Level')
    ax3.set_xlabel('Evolution Level')
    ax3.set_ylabel('Type')
    
    # 4. Centrality Correlations
    ax4 = fig.add_subplot(gs[1, :2])
    centrality_data = pd.DataFrame(data['centrality_scores'])
    scatter_matrix = pd.plotting.scatter_matrix(
        centrality_data[['degree', 'betweenness', 'closeness', 'eigenvector']],
        ax=ax4, diagonal='kde', alpha=0.5
    )
    ax4.set_title('Centrality Measure Correlations')
    
    # 5. Community Size Distribution
    ax5 = fig.add_subplot(gs[1, 2])
    community_sizes = data['community_sizes']
    ax5.pie(community_sizes, labels=[f'C{i+1}' for i in range(len(community_sizes))],
            autopct='%1.1f%%', startangle=90)
    ax5.set_title('Community Size Distribution')
    
    # 6. Clustering Coefficient by Degree
    ax6 = fig.add_subplot(gs[2, :])
    clustering_by_degree = data['clustering_by_degree']
    ax6.scatter(clustering_by_degree['degree'], 
                clustering_by_degree['clustering'],
                alpha=0.5, s=30)
    ax6.set_xlabel('Node Degree')
    ax6.set_ylabel('Clustering Coefficient')
    ax6.set_title('Local Clustering vs Node Degree')
    ax6.set_xscale('log')
    
    # Add trend line
    z = np.polyfit(np.log(clustering_by_degree['degree']), 
                   clustering_by_degree['clustering'], 1)
    p = np.poly1d(z)
    ax6.plot(clustering_by_degree['degree'], 
             p(np.log(clustering_by_degree['degree'])), 
             "r--", alpha=0.8)
    
    plt.suptitle('Digimon Network Statistical Analysis Dashboard', 
                 fontsize=20, fontweight='bold')
    
    return fig
```

### 6.2 Evolution Flow Visualization

**Sankey Diagram for Evolution Flow**
```python
def create_evolution_sankey(evolution_data):
    """
    Sankey diagram showing evolution level transitions
    """
    import plotly.graph_objects as go
    
    # Prepare data
    levels = ['Baby', 'In-Training', 'Rookie', 'Champion', 'Ultimate', 'Mega']
    
    # Create node labels
    labels = []
    for i, level in enumerate(levels):
        labels.extend([f"{level}_{j}" for j in range(evolution_data[level])])
    
    # Create links
    source = []
    target = []
    value = []
    link_color = []
    
    for link in evolution_data['transitions']:
        source.append(link['source_idx'])
        target.append(link['target_idx'])
        value.append(link['count'])
        
        # Color based on transition type
        if link['maintains_type']:
            link_color.append('rgba(0, 176, 246, 0.4)')  # Blue for type-maintaining
        else:
            link_color.append('rgba(255, 0, 104, 0.4)')  # Red for type-changing
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=[TYPE_COLOR_SYSTEM.get(node_type, {'primary': '#718096'})['primary'] 
                   for node_type in evolution_data['node_types']]
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_color
        )
    )])
    
    fig.update_layout(
        title="Evolution Flow Across Digimon Levels",
        font_size=12,
        height=800,
        width=1200
    )
    
    return fig
```

---

## 7. Machine Learning Visualizations

### 7.1 Model Performance Dashboard

**Comprehensive ML Results Visualization**
```python
def create_ml_performance_dashboard(results):
    """
    Multi-panel ML model performance visualization
    """
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 4, hspace=0.4, wspace=0.3)
    
    # 1. ROC Curves Comparison
    ax1 = fig.add_subplot(gs[0, :2])
    for model_name, model_results in results.items():
        fpr, tpr = model_results['roc_curve']
        auc = model_results['auc']
        ax1.plot(fpr, tpr, label=f'{model_name} (AUC = {auc:.3f})')
    
    ax1.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    ax1.set_xlabel('False Positive Rate')
    ax1.set_ylabel('True Positive Rate')
    ax1.set_title('ROC Curves Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Confusion Matrix for Best Model
    ax2 = fig.add_subplot(gs[0, 2:])
    best_model = max(results.items(), key=lambda x: x[1]['accuracy'])[0]
    cm = results[best_model]['confusion_matrix']
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax2)
    ax2.set_title(f'Confusion Matrix - {best_model}')
    ax2.set_xlabel('Predicted')
    ax2.set_ylabel('Actual')
    
    # 3. Feature Importance
    ax3 = fig.add_subplot(gs[1, :])
    feature_importance = results[best_model]['feature_importance']
    top_features = sorted(feature_importance.items(), 
                         key=lambda x: x[1], reverse=True)[:20]
    
    features, importance = zip(*top_features)
    y_pos = np.arange(len(features))
    
    ax3.barh(y_pos, importance, color='lightcoral')
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(features)
    ax3.set_xlabel('Importance Score')
    ax3.set_title('Top 20 Most Important Features')
    ax3.grid(True, axis='x', alpha=0.3)
    
    # 4. Learning Curves
    ax4 = fig.add_subplot(gs[2, :2])
    for model_name, model_results in results.items():
        train_sizes = model_results['learning_curve']['train_sizes']
        train_scores = model_results['learning_curve']['train_scores_mean']
        val_scores = model_results['learning_curve']['val_scores_mean']
        
        ax4.plot(train_sizes, train_scores, 'o-', label=f'{model_name} (train)')
        ax4.plot(train_sizes, val_scores, 's--', label=f'{model_name} (val)')
    
    ax4.set_xlabel('Training Set Size')
    ax4.set_ylabel('Score')
    ax4.set_title('Learning Curves')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Model Comparison Radar Chart
    ax5 = fig.add_subplot(gs[2, 2:], projection='polar')
    
    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'Training Time']
    num_vars = len(metrics)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    metrics += metrics[:1]
    angles += angles[:1]
    
    for model_name, model_results in results.items():
        values = [
            model_results['accuracy'],
            model_results['precision'],
            model_results['recall'],
            model_results['f1_score'],
            1 - (model_results['training_time'] / max_time)  # Normalized
        ]
        values += values[:1]
        
        ax5.plot(angles, values, 'o-', linewidth=2, label=model_name)
        ax5.fill(angles, values, alpha=0.25)
    
    ax5.set_xticks(angles[:-1])
    ax5.set_xticklabels(metrics[:-1])
    ax5.set_ylim(0, 1)
    ax5.set_title('Model Performance Comparison')
    ax5.legend()
    ax5.grid(True)
    
    plt.suptitle('Machine Learning Model Performance Dashboard', 
                 fontsize=20, fontweight='bold')
    
    return fig
```

### 7.2 SHAP Value Visualization

**Feature Interpretation with SHAP**
```python
def create_shap_visualizations(model, X_test, feature_names):
    """
    Create SHAP value visualizations for model interpretation
    """
    import shap
    
    # Create explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    # Summary plot
    fig1, ax1 = plt.subplots(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test, 
                      feature_names=feature_names,
                      show=False)
    plt.title('SHAP Summary Plot - Feature Impact on Model Output')
    
    # Waterfall plot for specific instance
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    shap.waterfall_plot(shap.Explanation(values=shap_values[0],
                                        base_values=explainer.expected_value,
                                        data=X_test.iloc[0],
                                        feature_names=feature_names),
                        show=False)
    plt.title('SHAP Waterfall Plot - Single Prediction Breakdown')
    
    # Dependence plots for top features
    fig3, axes = plt.subplots(2, 2, figsize=(12, 10))
    top_features = ['degree_centrality', 'type_Dragon', 
                    'evolution_out_degree', 'num_moves']
    
    for idx, feature in enumerate(top_features):
        ax = axes.flatten()[idx]
        shap.dependence_plot(feature, shap_values, X_test,
                            feature_names=feature_names,
                            ax=ax, show=False)
    
    plt.suptitle('SHAP Dependence Plots - Feature Interactions')
    
    return fig1, fig2, fig3
```

---

## 8. Dashboard Specifications

### 8.1 Main Interactive Dashboard

**Plotly Dash Application Structure**
```python
def create_main_dashboard():
    """
    Main interactive dashboard for Digimon network analysis
    """
    import dash
    from dash import dcc, html, Input, Output
    import plotly.express as px
    
    app = dash.Dash(__name__)
    
    app.layout = html.Div([
        # Header
        html.Div([
            html.H1('Digimon Network Analysis Dashboard',
                    style={'textAlign': 'center', 'color': '#2D3748'}),
            html.P('Explore 1,249 Digimon through Network Science',
                   style={'textAlign': 'center', 'color': '#718096'})
        ], style={'backgroundColor': '#F7FAFC', 'padding': '20px'}),
        
        # Control Panel
        html.Div([
            html.Div([
                html.Label('Select Analysis Type:'),
                dcc.Dropdown(
                    id='analysis-dropdown',
                    options=[
                        {'label': 'Network Overview', 'value': 'network'},
                        {'label': 'Evolution Analysis', 'value': 'evolution'},
                        {'label': 'Community Structure', 'value': 'community'},
                        {'label': 'Type Correlations', 'value': 'correlation'},
                        {'label': 'ML Predictions', 'value': 'ml'}
                    ],
                    value='network'
                )
            ], style={'width': '48%', 'display': 'inline-block'}),
            
            html.Div([
                html.Label('Filter by Type:'),
                dcc.Checklist(
                    id='type-filter',
                    options=[{'label': t, 'value': t} for t in TYPES],
                    value=TYPES[:5],
                    inline=True
                )
            ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
        ], style={'padding': '20px'}),
        
        # Main Visualization Area
        html.Div([
            dcc.Graph(id='main-graph', style={'height': '600px'})
        ]),
        
        # Statistics Panel
        html.Div([
            html.Div(id='stats-panel', children=[
                html.Div([
                    html.H3('Network Statistics'),
                    html.Div(id='network-stats')
                ], style={'width': '33%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3('Selected Node Info'),
                    html.Div(id='node-info')
                ], style={'width': '33%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3('Recommendations'),
                    html.Div(id='recommendations')
                ], style={'width': '33%', 'float': 'right', 'display': 'inline-block'})
            ])
        ], style={'backgroundColor': '#EDF2F7', 'padding': '20px', 'marginTop': '20px'})
    ])
    
    # Callbacks
    @app.callback(
        Output('main-graph', 'figure'),
        [Input('analysis-dropdown', 'value'),
         Input('type-filter', 'value')]
    )
    def update_main_graph(analysis_type, selected_types):
        # Logic to update visualization based on selection
        if analysis_type == 'network':
            return create_network_figure(selected_types)
        elif analysis_type == 'evolution':
            return create_evolution_figure(selected_types)
        elif analysis_type == 'community':
            return create_community_figure(selected_types)
        elif analysis_type == 'correlation':
            return create_correlation_figure(selected_types)
        elif analysis_type == 'ml':
            return create_ml_figure(selected_types)
    
    return app
```

### 8.2 Recommendation System Interface

**Interactive Recommendation Tool**
```python
def create_recommendation_interface():
    """
    Standalone recommendation system interface
    """
    import streamlit as st
    
    st.set_page_config(
        page_title="Digimon Recommendation System",
        page_icon="🎮",
        layout="wide"
    )
    
    # Sidebar
    st.sidebar.title("Recommendation Settings")
    
    # Select Digimon
    selected_digimon = st.sidebar.selectbox(
        "Choose a Digimon:",
        options=digimon_list,
        format_func=lambda x: f"{x['name_en']} ({x['type']})"
    )
    
    # Recommendation strategy
    strategy = st.sidebar.radio(
        "Recommendation Strategy:",
        ["Similar Digimon", "Evolution Partners", 
         "Team Composition", "Counter Picks"]
    )
    
    # Number of recommendations
    num_recommendations = st.sidebar.slider(
        "Number of Recommendations:",
        min_value=5, max_value=20, value=10
    )
    
    # Main content
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Selected Digimon")
        display_digimon_card(selected_digimon)
        
        # Show stats
        st.subheader("Statistics")
        stats = get_digimon_stats(selected_digimon)
        for stat, value in stats.items():
            st.metric(stat, value)
    
    with col2:
        st.subheader(f"{strategy} Recommendations")
        
        # Get recommendations
        recommendations = get_recommendations(
            selected_digimon, 
            strategy=strategy,
            k=num_recommendations
        )
        
        # Display as grid
        cols = st.columns(4)
        for idx, rec in enumerate(recommendations):
            with cols[idx % 4]:
                display_recommendation_card(rec)
        
        # Visualization
        st.subheader("Similarity Network")
        fig = create_similarity_network(
            selected_digimon, 
            recommendations
        )
        st.plotly_chart(fig, use_container_width=True)
```

---

## 9. Publication Guidelines

### 9.1 Figure Standards

**Publication-Ready Figure Template**
```python
def create_publication_figure(data, figure_type='main'):
    """
    Create publication-quality figures with consistent styling
    """
    # Set publication style
    plt.style.use('seaborn-v0_8-paper')
    
    # Configure matplotlib
    plt.rcParams.update({
        'font.size': 10,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 16,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans'],
        'axes.linewidth': 1.5,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1
    })
    
    if figure_type == 'main':
        fig, ax = plt.subplots(figsize=(7.5, 5))  # Single column width
    elif figure_type == 'double':
        fig, ax = plt.subplots(figsize=(15, 5))   # Double column width
    elif figure_type == 'square':
        fig, ax = plt.subplots(figsize=(5, 5))    # Square figure
    
    return fig, ax
```

### 9.2 Color Accessibility

**Color-Blind Friendly Palettes**
```python
COLORBLIND_SAFE_COLORS = {
    'categorical': [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#bcbd22',  # Olive
        '#17becf'   # Cyan
    ],
    'sequential': 'viridis',  # Or 'cividis'
    'diverging': 'RdBu'       # Red-Blue diverging
}
```

---

## 10. Implementation Examples

### 10.1 Complete Visualization Pipeline

```python
class DigimonVisualizationPipeline:
    """
    Complete visualization pipeline for Digimon analysis
    """
    
    def __init__(self, neo4j_connection):
        self.conn = neo4j_connection
        self.data = {}
        self.figures = {}
        
    def load_data(self):
        """Load all necessary data from Neo4j"""
        self.data['network'] = self.load_network()
        self.data['statistics'] = self.compute_statistics()
        self.data['communities'] = self.detect_communities()
        self.data['ml_results'] = self.load_ml_results()
        
    def create_all_visualizations(self):
        """Generate all visualizations for the article"""
        # Static visualizations
        self.figures['level_distribution'] = self.create_level_distribution()
        self.figures['type_correlation'] = self.create_type_correlation_matrix()
        self.figures['evolution_flow'] = self.create_evolution_sankey()
        self.figures['community_structure'] = self.create_3d_communities()
        self.figures['centrality_comparison'] = self.create_centrality_radar()
        self.figures['ml_performance'] = self.create_ml_dashboard()
        
        # Interactive visualizations
        self.figures['network_explorer'] = self.create_interactive_network()
        self.figures['recommendation_tool'] = self.create_recommendation_interface()
        self.figures['main_dashboard'] = self.create_main_dashboard()
        
    def export_for_publication(self, output_dir='./publication_figures'):
        """Export all figures in publication format"""
        os.makedirs(output_dir, exist_ok=True)
        
        for name, fig in self.figures.items():
            if isinstance(fig, plt.Figure):
                # Matplotlib figures
                fig.savefig(f"{output_dir}/{name}.png", dpi=300, bbox_inches='tight')
                fig.savefig(f"{output_dir}/{name}.pdf", bbox_inches='tight')
            elif hasattr(fig, 'write_html'):
                # Plotly figures
                fig.write_html(f"{output_dir}/{name}.html")
                fig.write_image(f"{output_dir}/{name}.png", scale=2)
            
    def generate_visualization_report(self):
        """Generate report documenting all visualizations"""
        report = {
            'total_figures': len(self.figures),
            'static_figures': sum(1 for f in self.figures.values() 
                                if isinstance(f, plt.Figure)),
            'interactive_figures': sum(1 for f in self.figures.values() 
                                     if hasattr(f, 'write_html')),
            'file_sizes': self.calculate_file_sizes(),
            'color_usage': self.analyze_color_usage(),
            'accessibility_check': self.check_accessibility()
        }
        
        return report
```

### 10.2 Visualization Best Practices Checklist

```python
def visualization_quality_check(figure):
    """
    Check visualization against best practices
    """
    checks = {
        'has_title': check_title(figure),
        'has_labels': check_axis_labels(figure),
        'readable_fonts': check_font_sizes(figure),
        'appropriate_colors': check_color_contrast(figure),
        'no_chartjunk': check_minimal_design(figure),
        'clear_legend': check_legend(figure),
        'proper_scale': check_scale_appropriateness(figure),
        'annotations': check_key_point_annotations(figure)
    }
    
    score = sum(checks.values()) / len(checks) * 100
    
    return {
        'score': score,
        'checks': checks,
        'recommendations': generate_improvement_suggestions(checks)
    }
```

---

**End of Visualization Guide**

This comprehensive visualization guide provides all the specifications, examples, and best practices needed to create compelling visualizations for your Digimon network analysis article. Each visualization is designed to support the narrative while maintaining scientific rigor and accessibility.