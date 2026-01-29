"""
inputless-graph - neo4j_repository.py

Neo4j database repository for behavioral event storage and querying.
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class Neo4jConfig(BaseModel):
    """Configuration for Neo4j connection"""

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="password", description="Neo4j password")
    database: Optional[str] = Field(default=None, description="Database name (optional)")
    max_connection_lifetime: int = Field(
        default=3600, description="Connection lifetime in seconds"
    )
    max_connection_pool_size: int = Field(
        default=50, description="Maximum connection pool size"
    )


class Neo4jRepository:
    """
    Repository for Neo4j graph database operations.

    Handles node creation, relationship management, and graph queries.
    """

    def __init__(self, config: Optional[Neo4jConfig] = None):
        """
        Initialize Neo4j repository.

        Args:
            config: Neo4j configuration (uses defaults if None)
        """
        self.config = config or Neo4jConfig()
        self.driver: Optional[Driver] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
            )
            # Verify connection
            with self.driver.session(database=self.config.database) as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.config.uri}")
        except Exception as e:
            error_msg = (
                f"Failed to connect to Neo4j at {self.config.uri}. "
                f"Error: {str(e)}. "
                f"Please verify: 1) Neo4j is running, 2) URI is correct, "
                f"3) Credentials are valid, 4) Network connectivity."
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e

    def close(self) -> None:
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def create_event_node(self, event: Dict[str, Any]) -> Optional[int]:
        """
        Create an Event node in Neo4j.

        Args:
            event: Event data dictionary with required keys: event_id, type, timestamp,
                   session_id. Optional keys: user_id, properties

        Returns:
            Node ID (internal Neo4j ID) or None if creation failed

        Raises:
            ValueError: If required event fields are missing
            RuntimeError: If database operation fails
        """
        # Validate required fields
        required_fields = ["event_id", "type", "timestamp", "session_id"]
        missing_fields = [field for field in required_fields if field not in event]
        if missing_fields:
            raise ValueError(
                f"Missing required event fields: {missing_fields}. "
                f"Required fields: {required_fields}"
            )
        query = """
        CREATE (e:Event {
            event_id: $event_id,
            type: $type,
            timestamp: $timestamp,
            session_id: $session_id,
            user_id: $user_id,
            properties: $properties
        })
        RETURN id(e) as node_id
        """

        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(
                    query,
                    event_id=event["event_id"],
                    type=event["type"],
                    timestamp=event["timestamp"],
                    session_id=event["session_id"],
                    user_id=event.get("user_id"),
                    properties=event.get("properties", {}),
                )
                record = result.single()
                if not record:
                    logger.warning(
                        f"Event node creation returned no result for event_id: {event['event_id']}"
                    )
                    return None
                return record["node_id"]
        except Exception as e:
            error_msg = (
                f"Failed to create event node for event_id '{event.get('event_id', 'unknown')}'. "
                f"Error: {str(e)}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def create_user_node(
        self, user_id: str, properties: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Create a User node in Neo4j.

        Args:
            user_id: Unique user identifier
            properties: Additional user properties

        Returns:
            Node ID or None if creation failed
        """
        query = """
        MERGE (u:User {user_id: $user_id})
        ON CREATE SET u.created_at = timestamp()
        SET u += $properties
        RETURN id(u) as node_id
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                query, user_id=user_id, properties=properties or {}
            )
            record = result.single()
            return record["node_id"] if record else None

    def connect_events(
        self,
        event1_id: str,
        event2_id: str,
        relationship_type: str = "FOLLOWED_BY",
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create relationship between two events.

        Args:
            event1_id: First event ID
            event2_id: Second event ID
            relationship_type: Type of relationship (FOLLOWED_BY, SIMILAR_TO, etc.)
            properties: Relationship properties (e.g., time_delta, similarity_score)

        Raises:
            ValueError: If relationship type is invalid or event IDs are empty
            RuntimeError: If relationship creation fails
        """
        if not event1_id or not event2_id:
            raise ValueError(
                "Both event1_id and event2_id must be non-empty strings"
            )

        # Sanitize relationship type to prevent injection
        if not relationship_type or not all(c.isalnum() or c == '_' for c in relationship_type):
            raise ValueError(
                f"Invalid relationship type: '{relationship_type}'. "
                f"Relationship type must contain only alphanumeric characters and underscores."
            )

        query = f"""
        MATCH (e1:Event {{event_id: $event1_id}})
        MATCH (e2:Event {{event_id: $event2_id}})
        MERGE (e1)-[r:{relationship_type}]->(e2)
        SET r += $properties
        """

        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(
                    query,
                    event1_id=event1_id,
                    event2_id=event2_id,
                    properties=properties or {},
                )
                # Consume result to ensure query executes
                result.consume()
        except Exception as e:
            error_msg = (
                f"Failed to create relationship '{relationship_type}' "
                f"between events '{event1_id}' and '{event2_id}'. "
                f"Error: {str(e)}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def link_user_to_event(self, user_id: str, event_id: str) -> None:
        """
        Link user to event with PERFORMED relationship.

        Args:
            user_id: User identifier
            event_id: Event identifier
        """
        query = """
        MATCH (u:User {user_id: $user_id})
        MATCH (e:Event {event_id: $event_id})
        MERGE (u)-[:PERFORMED]->(e)
        """

        with self.driver.session(database=self.config.database) as session:
            session.run(query, user_id=user_id, event_id=event_id)

    def find_event_sequences(
        self,
        session_id: str,
        min_length: int = 2,
        max_length: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Find event sequences for a session.

        Args:
            session_id: Session identifier
            min_length: Minimum sequence length
            max_length: Maximum sequence length

        Returns:
            List of event sequences, each containing list of events
        """
        query = """
        MATCH path = (start:Event {session_id: $session_id})-[:FOLLOWED_BY*1..10]->(end:Event)
        WHERE start.session_id = $session_id AND end.session_id = $session_id
          AND length(path) >= $min_length AND length(path) <= $max_length
        RETURN [node in nodes(path) | {
            event_id: node.event_id,
            type: node.type,
            timestamp: node.timestamp,
            properties: node.properties
        }] as sequence,
        length(path) as sequence_length
        ORDER BY sequence_length DESC
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                query,
                session_id=session_id,
                min_length=min_length,
                max_length=max_length,
            )
            return [record["sequence"] for record in result]

    def find_user_journey(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Find complete user journey across all sessions.

        Args:
            user_id: User identifier

        Returns:
            List of events in chronological order
        """
        query = """
        MATCH (u:User {user_id: $user_id})-[:PERFORMED]->(e:Event)
        RETURN e
        ORDER BY e.timestamp ASC
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, user_id=user_id)
            return [
                {
                    "event_id": record["e"]["event_id"],
                    "type": record["e"]["type"],
                    "timestamp": record["e"]["timestamp"],
                    "session_id": record["e"]["session_id"],
                }
                for record in result
            ]

    def find_similar_events(
        self, event_id: str, similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find events similar to given event.

        Args:
            event_id: Event identifier
            similarity_threshold: Minimum similarity score

        Returns:
            List of similar events with similarity scores
        """
        query = """
        MATCH (e1:Event {event_id: $event_id})-[r:SIMILAR_TO]->(e2:Event)
        WHERE r.similarity_score >= $threshold
        RETURN e2, r.similarity_score as similarity
        ORDER BY similarity DESC
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                query, event_id=event_id, threshold=similarity_threshold
            )
            return [
                {
                    "event_id": record["e2"]["event_id"],
                    "type": record["e2"]["type"],
                    "similarity": record["similarity"],
                }
                for record in result
            ]

    def create_pattern_node(
        self, pattern_id: str, pattern_data: Dict[str, Any]
    ) -> Optional[int]:
        """
        Create a Pattern node.

        Args:
            pattern_id: Pattern identifier
            pattern_data: Pattern data (event_types, sequence, frequency, confidence, etc.)

        Returns:
            Node ID or None if creation failed
        """
        query = """
        CREATE (p:Pattern {
            pattern_id: $pattern_id,
            event_types: $event_types,
            sequence: $sequence,
            frequency: $frequency,
            confidence: $confidence,
            properties: $properties
        })
        RETURN id(p) as node_id
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                query,
                pattern_id=pattern_id,
                event_types=pattern_data.get("event_types", []),
                sequence=pattern_data.get("sequence", []),
                frequency=pattern_data.get("frequency", 0),
                confidence=pattern_data.get("confidence", 0.0),
                properties=pattern_data.get("properties", {}),
            )
            record = result.single()
            return record["node_id"] if record else None

    def link_pattern_to_events(
        self, pattern_id: str, event_ids: List[str]
    ) -> None:
        """
        Link pattern to events with CONTAINS relationship.

        Args:
            pattern_id: Pattern identifier
            event_ids: List of event identifiers
        """
        query = """
        MATCH (p:Pattern {pattern_id: $pattern_id})
        UNWIND $event_ids as event_id
        MATCH (e:Event {event_id: event_id})
        MERGE (p)-[:CONTAINS]->(e)
        """

        with self.driver.session(database=self.config.database) as session:
            session.run(query, pattern_id=pattern_id, event_ids=event_ids)

    def execute_cypher(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute raw Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query results as list of dictionaries
        """
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection"""
        self.close()
