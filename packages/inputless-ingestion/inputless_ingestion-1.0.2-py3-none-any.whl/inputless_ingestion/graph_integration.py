"""
Graph integration for storing documents and relationships in Neo4j.

Creates document nodes, entity relationships, and similarity graphs.
"""

from typing import Dict, Any, List, Optional

# Optional inputless_graph import
try:
    from inputless_graph import Neo4jRepository
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    Neo4jRepository = None

from .models import DocumentData, Entity, Topic
from .exceptions import GraphIntegrationError


class DocumentGraphIntegration:
    """
    Graph database integration for document storage and relationships.
    
    Stores documents, entities, and relationships in Neo4j graph database.
    """
    
    def __init__(self, neo4j_repo):
        """
        Initialize graph integration.
        
        Args:
            neo4j_repo: Neo4j repository instance
            
        Raises:
            ImportError: If inputless_graph is not installed
        """
        if not GRAPH_AVAILABLE:
            raise ImportError(
                "inputless_graph is not installed. Install it to use graph integration."
            )
        self.repo = neo4j_repo
    
    def create_document_node(
        self, document_data: DocumentData
    ) -> str:
        """
        Create document node in Neo4j.
        
        Args:
            document_data: Processed document data
            
        Returns:
            Document node ID
            
        Raises:
            GraphIntegrationError: If node creation fails
        """
        try:
            metadata = document_data.metadata
            
            # Create document node
            query = """
            CREATE (d:Document {
                id: $document_id,
                file_path: $file_path,
                file_type: $file_type,
                file_size: $file_size,
                mime_type: $mime_type,
                title: $title,
                author: $author,
                created_date: $created_date,
                text_preview: $text_preview,
                page_count: $page_count
            })
            RETURN d.id as document_id
            """
            
            document_id = f"doc_{metadata.file_path.replace('/', '_')}"
            text_preview = document_data.text[:500] if document_data.text else ""
            
            # Neo4jRepository.execute_cypher is synchronous
            result = self.repo.execute_cypher(
                query,
                {
                    "document_id": document_id,
                    "file_path": metadata.file_path,
                    "file_type": metadata.file_type,
                    "file_size": metadata.file_size,
                    "mime_type": metadata.mime_type,
                    "title": metadata.title or "",
                    "author": metadata.author or "",
                    "created_date": metadata.created_date or "",
                    "text_preview": text_preview,
                    "page_count": metadata.page_count or 0,
                },
            )
            
            if result:
                return document_id
            else:
                return document_id  # Return ID even if query didn't return result
        except Exception as e:
            raise GraphIntegrationError(f"Failed to create document node: {str(e)}") from e
    
    def create_entity_nodes(
        self, document_id: str, entities: List[Entity]
    ) -> List[str]:
        """
        Create entity nodes and link to document.
        
        Args:
            document_id: Document node ID
            entities: List of entities
            
        Returns:
            List of entity node IDs
            
        Raises:
            GraphIntegrationError: If entity node creation fails
        """
        try:
            entity_ids = []
            
            for entity in entities:
                # Create or merge entity node
                query = """
                MERGE (e:Entity {text: $text, label: $label})
                ON CREATE SET e.confidence = $confidence
                ON MATCH SET e.confidence = CASE 
                    WHEN e.confidence < $confidence THEN $confidence 
                    ELSE e.confidence 
                END
                WITH e
                MATCH (d:Document {id: $document_id})
                MERGE (d)-[:CONTAINS_ENTITY]->(e)
                RETURN e.text as entity_id
                """
                
                result = self.repo.execute_cypher(
                    query,
                    {
                        "text": entity.text,
                        "label": entity.label,
                        "confidence": entity.confidence,
                        "document_id": document_id,
                    },
                )
                
                entity_ids.append(entity.text)
            
            return entity_ids
        except Exception as e:
            raise GraphIntegrationError(f"Failed to create entity nodes: {str(e)}") from e
    
    def create_topic_nodes(
        self, document_id: str, topics: List[Topic]
    ) -> List[str]:
        """
        Create topic nodes and link to document.
        
        Args:
            document_id: Document node ID
            topics: List of topics
            
        Returns:
            List of topic node IDs
            
        Raises:
            GraphIntegrationError: If topic node creation fails
        """
        try:
            topic_ids = []
            
            for topic in topics:
                # Create topic node
                query = """
                CREATE (t:Topic {
                    id: $topic_id,
                    keywords: $keywords,
                    weight: $weight
                })
                WITH t
                MATCH (d:Document {id: $document_id})
                MERGE (d)-[:HAS_TOPIC]->(t)
                RETURN t.id as topic_id
                """
                
                topic_id = f"topic_{document_id}_{topic.topic_id}"
                
                result = self.repo.execute_cypher(
                    query,
                    {
                        "topic_id": topic_id,
                        "keywords": topic.keywords,
                        "weight": topic.weight,
                        "document_id": document_id,
                    },
                )
                
                topic_ids.append(topic_id)
            
            return topic_ids
        except Exception as e:
            raise GraphIntegrationError(f"Failed to create topic nodes: {str(e)}") from e
    
    def find_similar_documents(
        self, document_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar documents based on shared entities and topics.
        
        Args:
            document_id: Document node ID
            limit: Maximum number of similar documents
            
        Returns:
            List of similar documents
            
        Raises:
            GraphIntegrationError: If query fails
        """
        try:
            query = """
            MATCH (d1:Document {id: $document_id})-[:CONTAINS_ENTITY]->(e:Entity)<-[:CONTAINS_ENTITY]-(d2:Document)
            WHERE d1.id <> d2.id
            WITH d2, count(e) as shared_entities
            ORDER BY shared_entities DESC
            LIMIT $limit
            RETURN d2.id as document_id, d2.file_path as file_path, shared_entities
            """
            
            results = self.repo.execute_cypher(
                query, {"document_id": document_id, "limit": limit}
            )
            
            return [
                {
                    "document_id": r["document_id"],
                    "file_path": r["file_path"],
                    "similarity_score": r["shared_entities"],
                }
                for r in results
            ]
        except Exception as e:
            raise GraphIntegrationError(f"Failed to find similar documents: {str(e)}") from e
