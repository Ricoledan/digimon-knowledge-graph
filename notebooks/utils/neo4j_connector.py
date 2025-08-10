"""
Neo4j connector utilities for Digimon Knowledge Graph analysis.
Provides connection management, query execution, and data extraction.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from neo4j import GraphDatabase, Result
from contextlib import contextmanager
import yaml
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)


class Neo4jConnector:
    """Manages Neo4j database connections and queries."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Neo4j connector.
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "analysis_config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.uri = self.config['neo4j']['uri']
        self.user = self.config['neo4j']['user']
        self.password = self.config['neo4j']['password']
        self.database = self.config['neo4j'].get('database', 'neo4j')
        self._driver = None
        
    def connect(self):
        """Establish connection to Neo4j database."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            logger.info(f"Connected to Neo4j at {self.uri}")
    
    def close(self):
        """Close database connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Closed Neo4j connection")
    
    @contextmanager
    def get_session(self):
        """Context manager for Neo4j sessions."""
        self.connect()
        session = self._driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of dictionaries containing query results
        """
        with self.get_session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def get_node_count(self, label: Optional[str] = None) -> int:
        """Get count of nodes with optional label filter."""
        if label:
            query = f"MATCH (n:{label}) RETURN count(n) as count"
        else:
            query = "MATCH (n) RETURN count(n) as count"
        
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_relationship_count(self, rel_type: Optional[str] = None) -> int:
        """Get count of relationships with optional type filter."""
        if rel_type:
            query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
        else:
            query = "MATCH ()-[r]->() RETURN count(r) as count"
        
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_all_digimon(self) -> pd.DataFrame:
        """Retrieve all Digimon with their properties."""
        query = """
        MATCH (d:Digimon)
        OPTIONAL MATCH (d)-[:HAS_LEVEL]->(level:Level)
        OPTIONAL MATCH (d)-[:HAS_TYPE]->(type:Type)
        OPTIONAL MATCH (d)-[:HAS_ATTRIBUTE]->(attr:Attribute)
        RETURN d.name_en as name_en,
               d.name_jp as name_jp,
               d.profile_en as profile_en,
               d.profile_jp as profile_jp,
               d.image_url as image_url,
               level.name_en as level,
               type.name_en as type,
               attr.name_en as attribute
        ORDER BY d.name_en
        """
        
        results = self.execute_query(query)
        return pd.DataFrame(results)
    
    def get_evolution_chains(self) -> List[Dict[str, Any]]:
        """Get all evolution relationships."""
        query = """
        MATCH (from:Digimon)-[r:RELATED_TO]->(to:Digimon)
        RETURN from.name_en as from_digimon,
               to.name_en as to_digimon,
               r.relationship_type as type
        """
        
        return self.execute_query(query)
    
    def get_digimon_moves(self) -> pd.DataFrame:
        """Get all Digimon-Move relationships."""
        query = """
        MATCH (d:Digimon)-[:CAN_USE]->(m:Move)
        RETURN d.name_en as digimon,
               m.name_en as move,
               m.name_jp as move_jp
        ORDER BY d.name_en, m.name_en
        """
        
        results = self.execute_query(query)
        return pd.DataFrame(results)
    
    def get_type_distribution(self) -> pd.DataFrame:
        """Get distribution of Digimon types."""
        query = """
        MATCH (d:Digimon)-[:HAS_TYPE]->(t:Type)
        RETURN t.name_en as type, count(d) as count
        ORDER BY count DESC
        """
        
        results = self.execute_query(query)
        return pd.DataFrame(results)
    
    def get_attribute_distribution(self) -> pd.DataFrame:
        """Get distribution of Digimon attributes."""
        query = """
        MATCH (d:Digimon)-[:HAS_ATTRIBUTE]->(a:Attribute)
        RETURN a.name_en as attribute, count(d) as count
        ORDER BY count DESC
        """
        
        results = self.execute_query(query)
        return pd.DataFrame(results)
    
    def get_level_distribution(self) -> pd.DataFrame:
        """Get distribution of Digimon levels."""
        query = """
        MATCH (d:Digimon)-[:HAS_LEVEL]->(l:Level)
        RETURN l.name_en as level, count(d) as count
        ORDER BY count DESC
        """
        
        results = self.execute_query(query)
        return pd.DataFrame(results)
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        stats = {
            'total_nodes': self.get_node_count(),
            'total_relationships': self.get_relationship_count(),
            'digimon_count': self.get_node_count('Digimon'),
            'type_count': self.get_node_count('Type'),
            'attribute_count': self.get_node_count('Attribute'),
            'level_count': self.get_node_count('Level'),
            'move_count': self.get_node_count('Move'),
        }
        
        # Get relationship counts
        rel_types = ['HAS_TYPE', 'HAS_ATTRIBUTE', 'HAS_LEVEL', 'CAN_USE', 'RELATED_TO']
        for rel_type in rel_types:
            stats[f'{rel_type.lower()}_count'] = self.get_relationship_count(rel_type)
        
        return stats
    
    def export_to_networkx(self, node_labels: Optional[List[str]] = None, 
                          rel_types: Optional[List[str]] = None):
        """
        Export Neo4j graph to NetworkX format.
        
        Args:
            node_labels: List of node labels to include (None for all)
            rel_types: List of relationship types to include (None for all)
            
        Returns:
            NetworkX graph object
        """
        import networkx as nx
        
        # Build query
        node_filter = f":{':'.join(node_labels)}" if node_labels else ""
        rel_filter = f":{':'.join(rel_types)}" if rel_types else ""
        
        query = f"""
        MATCH (n{node_filter})-[r{rel_filter}]->(m)
        RETURN n, r, m
        """
        
        G = nx.DiGraph()
        
        with self.get_session() as session:
            result = session.run(query)
            
            for record in result:
                # Add nodes
                n_props = dict(record['n'])
                m_props = dict(record['m'])
                
                n_id = n_props.get('name_en', record['n'].id)
                m_id = m_props.get('name_en', record['m'].id)
                
                G.add_node(n_id, **n_props)
                G.add_node(m_id, **m_props)
                
                # Add edge
                r_props = dict(record['r'])
                G.add_edge(n_id, m_id, **r_props)
        
        return G
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions
def test_connection(config_path: Optional[str] = None) -> bool:
    """Test Neo4j connection."""
    try:
        with Neo4jConnector(config_path) as conn:
            stats = conn.get_graph_statistics()
            logger.info(f"Connection successful. Found {stats['digimon_count']} Digimon")
            return True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False


def get_digimon_df(config_path: Optional[str] = None) -> pd.DataFrame:
    """Quick function to get all Digimon data."""
    with Neo4jConnector(config_path) as conn:
        return conn.get_all_digimon()