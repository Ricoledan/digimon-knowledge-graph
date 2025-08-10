"""
Graph algorithm utilities for Digimon Knowledge Graph analysis.
Provides network analysis, community detection, and graph metrics.
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import defaultdict, Counter
import community as community_louvain
from sklearn.metrics import silhouette_score
from sklearn.cluster import SpectralClustering
import logging

logger = logging.getLogger(__name__)


def calculate_basic_metrics(G: nx.Graph) -> Dict[str, Any]:
    """Calculate basic graph metrics."""
    metrics = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'density': nx.density(G),
        'is_connected': nx.is_connected(G) if not G.is_directed() else nx.is_weakly_connected(G),
        'num_components': nx.number_connected_components(G) if not G.is_directed() else nx.number_weakly_connected_components(G),
        'average_degree': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
    }
    
    # Additional metrics for directed graphs
    if G.is_directed():
        metrics['is_dag'] = nx.is_directed_acyclic_graph(G)
        metrics['num_strongly_connected'] = nx.number_strongly_connected_components(G)
    
    return metrics


def calculate_centrality_measures(G: nx.Graph, normalize: bool = True) -> pd.DataFrame:
    """Calculate various centrality measures for all nodes."""
    centrality_data = {}
    
    # Degree centrality
    centrality_data['degree'] = nx.degree_centrality(G)
    
    # Betweenness centrality
    try:
        centrality_data['betweenness'] = nx.betweenness_centrality(G, normalized=normalize)
    except:
        logger.warning("Betweenness centrality calculation failed")
        centrality_data['betweenness'] = {node: 0 for node in G.nodes()}
    
    # Closeness centrality
    try:
        centrality_data['closeness'] = nx.closeness_centrality(G)
    except:
        logger.warning("Closeness centrality calculation failed")
        centrality_data['closeness'] = {node: 0 for node in G.nodes()}
    
    # Eigenvector centrality
    try:
        centrality_data['eigenvector'] = nx.eigenvector_centrality(G, max_iter=1000)
    except:
        logger.warning("Eigenvector centrality calculation failed")
        centrality_data['eigenvector'] = {node: 0 for node in G.nodes()}
    
    # PageRank
    try:
        centrality_data['pagerank'] = nx.pagerank(G)
    except:
        logger.warning("PageRank calculation failed")
        centrality_data['pagerank'] = {node: 0 for node in G.nodes()}
    
    # Convert to DataFrame
    df = pd.DataFrame(centrality_data)
    df.index.name = 'node'
    
    # Add in/out degree for directed graphs
    if G.is_directed():
        df['in_degree'] = pd.Series(dict(G.in_degree()))
        df['out_degree'] = pd.Series(dict(G.out_degree()))
    
    return df


def detect_communities_louvain(G: nx.Graph, resolution: float = 1.0) -> Dict[int, List[str]]:
    """Detect communities using Louvain method."""
    # Convert to undirected if necessary
    G_undirected = G.to_undirected() if G.is_directed() else G
    
    # Apply Louvain
    partition = community_louvain.best_partition(G_undirected, resolution=resolution)
    
    # Convert to community dict
    communities = defaultdict(list)
    for node, comm_id in partition.items():
        communities[comm_id].append(node)
    
    return dict(communities)


def detect_communities_label_propagation(G: nx.Graph) -> Dict[int, List[str]]:
    """Detect communities using label propagation."""
    G_undirected = G.to_undirected() if G.is_directed() else G
    
    communities_generator = nx.community.label_propagation_communities(G_undirected)
    communities = {}
    
    for i, community in enumerate(communities_generator):
        communities[i] = list(community)
    
    return communities


def detect_communities_girvan_newman(G: nx.Graph, num_communities: int = None) -> Dict[int, List[str]]:
    """Detect communities using Girvan-Newman algorithm."""
    G_undirected = G.to_undirected() if G.is_directed() else G
    
    # Get communities generator
    communities_generator = nx.community.girvan_newman(G_undirected)
    
    # Get desired number of communities
    if num_communities is None:
        # Use modularity to find optimal number
        best_modularity = -1
        best_communities = None
        
        for i, communities in enumerate(communities_generator):
            if i >= 10:  # Limit iterations
                break
            
            modularity = nx.community.modularity(G_undirected, communities)
            if modularity > best_modularity:
                best_modularity = modularity
                best_communities = communities
        
        communities = best_communities
    else:
        # Get specific number of communities
        for i, comm in enumerate(communities_generator):
            if len(comm) >= num_communities:
                communities = comm
                break
    
    # Convert to dict format
    result = {}
    for i, community in enumerate(communities):
        result[i] = list(community)
    
    return result


def calculate_modularity(G: nx.Graph, communities: Dict[int, List[str]]) -> float:
    """Calculate modularity score for given communities."""
    G_undirected = G.to_undirected() if G.is_directed() else G
    
    # Convert to format expected by networkx
    communities_list = [set(nodes) for nodes in communities.values()]
    
    return nx.community.modularity(G_undirected, communities_list)


def find_evolution_chains(G: nx.DiGraph, evolution_rel: str = 'EVOLVES_TO') -> List[List[str]]:
    """Find all evolution chains in the graph."""
    chains = []
    
    # Find all nodes with no incoming evolution edges (chain starts)
    chain_starts = []
    for node in G.nodes():
        incoming_evolutions = [e for e in G.in_edges(node) if G.edges[e].get('type') == evolution_rel]
        if not incoming_evolutions:
            # Check if this node has any outgoing evolution edges
            outgoing_evolutions = [e for e in G.out_edges(node) if G.edges[e].get('type') == evolution_rel]
            if outgoing_evolutions:
                chain_starts.append(node)
    
    # Build chains from each start
    def build_chain(start_node: str, current_chain: List[str], visited: Set[str]):
        current_chain.append(start_node)
        visited.add(start_node)
        
        # Find next nodes in evolution
        next_nodes = []
        for _, target in G.out_edges(start_node):
            if G.edges[(start_node, target)].get('type') == evolution_rel and target not in visited:
                next_nodes.append(target)
        
        if not next_nodes:
            # End of chain
            chains.append(current_chain.copy())
        else:
            # Continue building chain
            for next_node in next_nodes:
                build_chain(next_node, current_chain.copy(), visited.copy())
    
    # Build all chains
    for start in chain_starts:
        build_chain(start, [], set())
    
    return chains


def calculate_clustering_coefficient(G: nx.Graph) -> Dict[str, float]:
    """Calculate clustering coefficients."""
    G_undirected = G.to_undirected() if G.is_directed() else G
    
    return {
        'average_clustering': nx.average_clustering(G_undirected),
        'transitivity': nx.transitivity(G_undirected),
        'node_clustering': dict(nx.clustering(G_undirected))
    }


def find_bridges(G: nx.Graph) -> List[Tuple[str, str]]:
    """Find bridge edges in the graph."""
    G_undirected = G.to_undirected() if G.is_directed() else G
    return list(nx.bridges(G_undirected))


def find_articulation_points(G: nx.Graph) -> List[str]:
    """Find articulation points (cut vertices) in the graph."""
    G_undirected = G.to_undirected() if G.is_directed() else G
    return list(nx.articulation_points(G_undirected))


def calculate_path_statistics(G: nx.Graph, sample_size: int = 1000) -> Dict[str, float]:
    """Calculate path length statistics."""
    nodes = list(G.nodes())
    
    if len(nodes) < 2:
        return {'avg_shortest_path': 0, 'diameter': 0}
    
    # Sample paths for large graphs
    if len(nodes) > sample_size:
        sampled_nodes = np.random.choice(nodes, size=sample_size, replace=False)
    else:
        sampled_nodes = nodes
    
    path_lengths = []
    for i, source in enumerate(sampled_nodes):
        for target in sampled_nodes[i+1:]:
            try:
                length = nx.shortest_path_length(G, source, target)
                path_lengths.append(length)
            except nx.NetworkXNoPath:
                continue
    
    if path_lengths:
        return {
            'avg_shortest_path': np.mean(path_lengths),
            'diameter': max(path_lengths),
            'median_path_length': np.median(path_lengths),
            'std_path_length': np.std(path_lengths)
        }
    else:
        return {'avg_shortest_path': float('inf'), 'diameter': float('inf')}


def find_connected_components(G: nx.Graph) -> List[Set[str]]:
    """Find connected components in the graph."""
    if G.is_directed():
        return [set(comp) for comp in nx.weakly_connected_components(G)]
    else:
        return [set(comp) for comp in nx.connected_components(G)]


def calculate_degree_distribution(G: nx.Graph) -> pd.DataFrame:
    """Calculate degree distribution statistics."""
    degrees = [d for n, d in G.degree()]
    
    if G.is_directed():
        in_degrees = [d for n, d in G.in_degree()]
        out_degrees = [d for n, d in G.out_degree()]
        
        return pd.DataFrame({
            'degree': degrees,
            'in_degree': in_degrees,
            'out_degree': out_degrees
        })
    else:
        return pd.DataFrame({'degree': degrees})


def find_cliques(G: nx.Graph, min_size: int = 3) -> List[Set[str]]:
    """Find all maximal cliques of minimum size."""
    G_undirected = G.to_undirected() if G.is_directed() else G
    
    cliques = []
    for clique in nx.find_cliques(G_undirected):
        if len(clique) >= min_size:
            cliques.append(set(clique))
    
    return cliques


def calculate_assortativity(G: nx.Graph, attribute: str) -> float:
    """Calculate assortativity coefficient for a node attribute."""
    try:
        return nx.attribute_assortativity_coefficient(G, attribute)
    except:
        logger.warning(f"Could not calculate assortativity for attribute: {attribute}")
        return 0.0


def find_k_core(G: nx.Graph, k: int = None) -> nx.Graph:
    """Find k-core subgraph."""
    G_undirected = G.to_undirected() if G.is_directed() else G
    
    if k is None:
        # Find max-core
        return nx.k_core(G_undirected)
    else:
        return nx.k_core(G_undirected, k=k)


def calculate_rich_club_coefficient(G: nx.Graph, normalized: bool = True) -> Dict[int, float]:
    """Calculate rich club coefficient."""
    G_undirected = G.to_undirected() if G.is_directed() else G
    
    if normalized:
        return nx.rich_club_coefficient(G_undirected, normalized=True)
    else:
        return nx.rich_club_coefficient(G_undirected, normalized=False)