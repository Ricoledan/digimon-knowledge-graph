"""Main analysis module for Digimon knowledge graph."""

from typing import Dict, List, Any
from neo4j import GraphDatabase
from loguru import logger
from ..utils.config import config


class DigimonAnalyzer:
    """Analyze Digimon knowledge graph."""
    
    def __init__(self):
        """Initialize analyzer with Neo4j connection."""
        self.uri = config.get("neo4j.uri", "bolt://localhost:7687")
        self.user = config.get("neo4j.user", "neo4j")
        self.password = config.get("neo4j.password", "digimon123")
        self.driver = None
        
    def connect(self) -> bool:
        """Connect to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            logger.info(f"Connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
            
    def close(self):
        """Close connection."""
        if self.driver:
            self.driver.close()
            
    def run_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Run a Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]
            
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the graph."""
        stats = {}
        
        # Total counts
        queries = {
            "total_digimon": "MATCH (d:Digimon) RETURN count(d) as count",
            "total_levels": "MATCH (l:Level) RETURN count(l) as count",
            "total_types": "MATCH (t:Type) RETURN count(t) as count",
            "total_attributes": "MATCH (a:Attribute) RETURN count(a) as count",
            "total_moves": "MATCH (m:Move) RETURN count(m) as count",
            "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count"
        }
        
        for key, query in queries.items():
            result = self.run_query(query)
            stats[key] = result[0]["count"] if result else 0
            
        return stats
        
    def get_level_distribution(self) -> List[Dict]:
        """Get distribution of Digimon by level."""
        query = """
        MATCH (d:Digimon)-[:HAS_LEVEL]->(l:Level)
        RETURN l.name as level, l.name_en as level_en, count(d) as count
        ORDER BY count DESC
        """
        return self.run_query(query)
        
    def get_type_distribution(self) -> List[Dict]:
        """Get distribution of Digimon by type."""
        query = """
        MATCH (d:Digimon)-[:HAS_TYPE]->(t:Type)
        RETURN t.name as type, t.name_en as type_en, count(d) as count
        ORDER BY count DESC
        LIMIT 20
        """
        return self.run_query(query)
        
    def get_attribute_distribution(self) -> List[Dict]:
        """Get distribution of Digimon by attribute."""
        query = """
        MATCH (d:Digimon)-[:HAS_ATTRIBUTE]->(a:Attribute)
        RETURN a.name as attribute, a.name_en as attribute_en, count(d) as count
        ORDER BY count DESC
        """
        return self.run_query(query)
        
    def get_most_connected_digimon(self, limit: int = 10) -> List[Dict]:
        """Get Digimon with most relationships."""
        query = """
        MATCH (d:Digimon)-[r]-()
        WITH d, count(r) as connections
        RETURN d.name_en as name, d.name_jp as name_jp, connections
        ORDER BY connections DESC
        LIMIT $limit
        """
        return self.run_query(query, {"limit": limit})
        
    def get_shared_moves(self, limit: int = 10) -> List[Dict]:
        """Get moves shared by multiple Digimon."""
        query = """
        MATCH (d:Digimon)-[:CAN_USE]->(m:Move)
        WITH m, count(d) as digimon_count, collect(d.name_en) as digimon_names
        WHERE digimon_count > 1
        RETURN m.name as move, m.name_en as move_en, digimon_count, digimon_names[0..5] as sample_digimon
        ORDER BY digimon_count DESC
        LIMIT $limit
        """
        return self.run_query(query, {"limit": limit})
        
    def get_type_attribute_matrix(self) -> List[Dict]:
        """Get matrix of type-attribute combinations."""
        query = """
        MATCH (d:Digimon)-[:HAS_TYPE]->(t:Type)
        MATCH (d)-[:HAS_ATTRIBUTE]->(a:Attribute)
        WITH t.name_en as type, a.name_en as attribute, count(d) as count
        RETURN type, attribute, count
        ORDER BY type, attribute
        """
        return self.run_query(query)
        
    def find_digimon_clusters(self) -> List[Dict]:
        """Find clusters of related Digimon."""
        query = """
        MATCH (d1:Digimon)-[:SHARES_TYPE|SHARES_ATTRIBUTE|SHARES_MOVE]-(d2:Digimon)
        WITH d1, count(DISTINCT d2) as shared_count
        WHERE shared_count > 5
        RETURN d1.name_en as name, d1.type_en as type, d1.attribute_en as attribute, shared_count
        ORDER BY shared_count DESC
        LIMIT 20
        """
        return self.run_query(query)


def main():
    """Run basic analysis."""
    analyzer = DigimonAnalyzer()
    
    if not analyzer.connect():
        logger.error("Failed to connect to Neo4j. Make sure it's running!")
        return
        
    try:
        # Get basic stats
        logger.info("Fetching basic statistics...")
        stats = analyzer.get_basic_stats()
        
        print("\n" + "=" * 60)
        print("DIGIMON KNOWLEDGE GRAPH ANALYSIS")
        print("=" * 60)
        
        print("\n📊 BASIC STATISTICS:")
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value:,}")
            
        # Level distribution
        print("\n📈 LEVEL DISTRIBUTION:")
        levels = analyzer.get_level_distribution()
        for level in levels:
            print(f"  {level['level_en']} ({level['level']}): {level['count']} Digimon")
            
        # Type distribution (top 10)
        print("\n🏷️  TOP 10 TYPES:")
        types = analyzer.get_type_distribution()[:10]
        for type_info in types:
            print(f"  {type_info['type_en']} ({type_info['type']}): {type_info['count']} Digimon")
            
        # Attribute distribution
        print("\n⚡ ATTRIBUTE DISTRIBUTION:")
        attributes = analyzer.get_attribute_distribution()
        for attr in attributes:
            print(f"  {attr['attribute_en']} ({attr['attribute']}): {attr['count']} Digimon")
            
        # Most connected Digimon
        print("\n🔗 MOST CONNECTED DIGIMON:")
        connected = analyzer.get_most_connected_digimon()
        for digimon in connected:
            print(f"  {digimon['name']} ({digimon['name_jp']}): {digimon['connections']} connections")
            
        # Shared moves
        print("\n🎯 MOST SHARED MOVES:")
        moves = analyzer.get_shared_moves()
        for move in moves:
            print(f"  {move['move_en']} ({move['move']}): Used by {move['digimon_count']} Digimon")
            print(f"    Examples: {', '.join(move['sample_digimon'])}")
            
        print("\n" + "=" * 60)
        
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()