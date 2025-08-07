"""Neo4j data loader for Digimon knowledge graph."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from neo4j import GraphDatabase, Driver
from loguru import logger
from tqdm import tqdm

from ..utils.config import config


class DigimonGraphLoader:
    """Loads Digimon data into Neo4j graph database."""
    
    def __init__(self):
        """Initialize Neo4j connection."""
        self.uri = config.get("neo4j.uri", "bolt://localhost:7687")
        self.user = config.get("neo4j.user", "neo4j")
        self.password = config.get("neo4j.password", "digimon123")
        self.driver: Optional[Driver] = None
        
    def connect(self) -> bool:
        """Connect to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            logger.info(f"Connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
            
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")
            
    def create_constraints(self):
        """Create uniqueness constraints and indexes."""
        constraints = [
            # Unique constraints
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Digimon) REQUIRE d.directory_name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Level) REQUIRE l.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Type) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Attribute) REQUIRE a.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Move) REQUIRE m.name IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX IF NOT EXISTS FOR (d:Digimon) ON (d.name_en)",
            "CREATE INDEX IF NOT EXISTS FOR (d:Digimon) ON (d.name_jp)",
            "CREATE INDEX IF NOT EXISTS FOR (d:Digimon) ON (d.level)",
            "CREATE INDEX IF NOT EXISTS FOR (d:Digimon) ON (d.type)",
            "CREATE INDEX IF NOT EXISTS FOR (d:Digimon) ON (d.attribute)",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.debug(f"Created: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint might already exist: {e}")
                    
    def clear_database(self):
        """Clear all nodes and relationships from database."""
        logger.warning("Clearing entire database...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared")
            
    def load_digimon(self, digimon_data: Dict[str, Any]) -> bool:
        """Load a single Digimon into the graph."""
        try:
            with self.driver.session() as session:
                # Create Digimon node
                digimon_props = {
                    "directory_name": digimon_data["directory_name"],
                    "name_jp": digimon_data["names"]["japanese"],
                    "name_en": digimon_data["names"]["english"],
                    "level": digimon_data["info"]["level"],
                    "level_en": digimon_data["info"].get("level_en", digimon_data["info"]["level"]),
                    "type": digimon_data["info"]["type"],
                    "type_en": digimon_data["info"].get("type_en", digimon_data["info"]["type"]),
                    "attribute": digimon_data["info"]["attribute"],
                    "attribute_en": digimon_data["info"].get("attribute_en", digimon_data["info"]["attribute"]),
                    "profile_jp": digimon_data["profile"]["japanese"],
                    "profile_en": digimon_data["profile"].get("english", ""),
                    "image_url": digimon_data["images"]["main"],
                    "loaded_at": datetime.now().isoformat()
                }
                
                # Create Digimon node
                session.run("""
                    MERGE (d:Digimon {directory_name: $directory_name})
                    SET d = $props
                """, directory_name=digimon_props["directory_name"], props=digimon_props)
                
                # Create and link Level node
                session.run("""
                    MERGE (l:Level {name: $level})
                    SET l.name_en = $level_en
                    WITH l
                    MATCH (d:Digimon {directory_name: $directory_name})
                    MERGE (d)-[:HAS_LEVEL]->(l)
                """, level=digimon_data["info"]["level"], 
                    level_en=digimon_data["info"].get("level_en", digimon_data["info"]["level"]),
                    directory_name=digimon_data["directory_name"])
                
                # Create and link Type node
                session.run("""
                    MERGE (t:Type {name: $type})
                    SET t.name_en = $type_en
                    WITH t
                    MATCH (d:Digimon {directory_name: $directory_name})
                    MERGE (d)-[:HAS_TYPE]->(t)
                """, type=digimon_data["info"]["type"],
                    type_en=digimon_data["info"].get("type_en", digimon_data["info"]["type"]),
                    directory_name=digimon_data["directory_name"])
                
                # Create and link Attribute node
                session.run("""
                    MERGE (a:Attribute {name: $attribute})
                    SET a.name_en = $attribute_en
                    WITH a
                    MATCH (d:Digimon {directory_name: $directory_name})
                    MERGE (d)-[:HAS_ATTRIBUTE]->(a)
                """, attribute=digimon_data["info"]["attribute"],
                    attribute_en=digimon_data["info"].get("attribute_en", digimon_data["info"]["attribute"]),
                    directory_name=digimon_data["directory_name"])
                
                # Create and link Move nodes
                for move in digimon_data.get("special_moves", []):
                    move_en = digimon_data.get("special_moves_en", [])
                    move_en_name = move_en[digimon_data["special_moves"].index(move)] if move_en and len(move_en) > digimon_data["special_moves"].index(move) else move
                    
                    session.run("""
                        MERGE (m:Move {name: $move})
                        SET m.name_en = $move_en
                        WITH m
                        MATCH (d:Digimon {directory_name: $directory_name})
                        MERGE (d)-[:CAN_USE]->(m)
                    """, move=move, move_en=move_en_name, directory_name=digimon_data["directory_name"])
                
                # Create relationships to related Digimon
                for related in digimon_data.get("related_digimon", []):
                    session.run("""
                        MERGE (d2:Digimon {directory_name: $related_dir})
                        ON CREATE SET d2.name_jp = $related_name, d2.pending_load = true
                        WITH d2
                        MATCH (d1:Digimon {directory_name: $directory_name})
                        MERGE (d1)-[:RELATED_TO]->(d2)
                    """, directory_name=digimon_data["directory_name"],
                        related_dir=related["directory_name"],
                        related_name=related["name"])
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to load Digimon {digimon_data.get('names', {}).get('english', 'Unknown')}: {e}")
            return False
            
    def load_all_digimon(self, data_dir: Path) -> Dict[str, int]:
        """Load all Digimon from JSON files into Neo4j."""
        data_path = Path(data_dir)
        json_files = list(data_path.glob("*.json"))
        json_files = [f for f in json_files if not f.name.startswith("_")]
        
        logger.info(f"Found {len(json_files)} Digimon files to load")
        
        stats = {
            "total": len(json_files),
            "successful": 0,
            "failed": 0
        }
        
        # Create constraints first
        self.create_constraints()
        
        # Load each Digimon
        for json_file in tqdm(json_files, desc="Loading Digimon"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if self.load_digimon(data):
                    stats["successful"] += 1
                else:
                    stats["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Failed to process {json_file.name}: {e}")
                stats["failed"] += 1
                
        # Create additional relationships based on shared attributes
        self._create_shared_relationships()
        
        return stats
        
    def _create_shared_relationships(self):
        """Create relationships between Digimon that share attributes."""
        logger.info("Creating shared attribute relationships...")
        
        with self.driver.session() as session:
            # Digimon that share the same Type
            session.run("""
                MATCH (d1:Digimon)-[:HAS_TYPE]->(t:Type)<-[:HAS_TYPE]-(d2:Digimon)
                WHERE d1.directory_name < d2.directory_name
                MERGE (d1)-[:SHARES_TYPE {type: t.name}]->(d2)
            """)
            
            # Digimon that share the same Level
            session.run("""
                MATCH (d1:Digimon)-[:HAS_LEVEL]->(l:Level)<-[:HAS_LEVEL]-(d2:Digimon)
                WHERE d1.directory_name < d2.directory_name
                MERGE (d1)-[:SHARES_LEVEL {level: l.name}]->(d2)
            """)
            
            # Digimon that share the same Attribute
            session.run("""
                MATCH (d1:Digimon)-[:HAS_ATTRIBUTE]->(a:Attribute)<-[:HAS_ATTRIBUTE]-(d2:Digimon)
                WHERE d1.directory_name < d2.directory_name
                MERGE (d1)-[:SHARES_ATTRIBUTE {attribute: a.name}]->(d2)
            """)
            
            # Digimon that share special moves
            session.run("""
                MATCH (d1:Digimon)-[:CAN_USE]->(m:Move)<-[:CAN_USE]-(d2:Digimon)
                WHERE d1.directory_name < d2.directory_name
                MERGE (d1)-[:SHARES_MOVE {move: m.name}]->(d2)
            """)
            
            logger.info("Shared relationships created")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.driver.session() as session:
            stats = {}
            
            # Count nodes
            node_types = ["Digimon", "Level", "Type", "Attribute", "Move"]
            for node_type in node_types:
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                stats[f"{node_type.lower()}_count"] = result.single()["count"]
                
            # Count relationships
            rel_types = ["HAS_LEVEL", "HAS_TYPE", "HAS_ATTRIBUTE", "CAN_USE", 
                        "RELATED_TO", "SHARES_TYPE", "SHARES_LEVEL", "SHARES_ATTRIBUTE", "SHARES_MOVE"]
            for rel_type in rel_types:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                stats[f"{rel_type.lower()}_count"] = result.single()["count"]
                
            return stats


def main():
    """Main entry point for graph loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load Digimon data into Neo4j")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/translated",
        help="Directory containing translated Digimon JSON files"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear database before loading"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - only load first 10 Digimon"
    )
    args = parser.parse_args()
    
    loader = DigimonGraphLoader()
    
    # Connect to Neo4j
    if not loader.connect():
        logger.error("Failed to connect to Neo4j. Make sure it's running!")
        logger.info("Start Neo4j with: ./scripts/database/start_neo4j.sh")
        return
        
    try:
        # Clear database if requested
        if args.clear:
            loader.clear_database()
            
        # Get data directory
        data_dir = Path(args.data_dir)
        if args.test:
            data_dir = data_dir / "test"
            
        if not data_dir.exists():
            logger.error(f"Data directory not found: {data_dir}")
            return
            
        # Load data
        logger.info(f"Loading data from: {data_dir}")
        stats = loader.load_all_digimon(data_dir)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Graph loading complete!")
        logger.info(f"Total Digimon: {stats['total']}")
        logger.info(f"Successfully loaded: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        
        # Get database stats
        db_stats = loader.get_stats()
        logger.info("\nDatabase statistics:")
        for key, value in db_stats.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 60)
        
    finally:
        loader.close()
        

if __name__ == "__main__":
    main()