"""
inputless-graph - graph_queries.py

Cypher query builders for graph operations.
"""

from typing import Optional


class GraphQueries:
    """Builder for common Cypher queries"""

    @staticmethod
    def find_event_sequences_query(
        session_id: str, min_length: int = 2, max_length: int = 10
    ) -> str:
        """
        Build query to find event sequences.

        Args:
            session_id: Session identifier
            min_length: Minimum sequence length
            max_length: Maximum sequence length

        Returns:
            Cypher query string
        """
        return f"""
        MATCH path = (start:Event {{session_id: $session_id}})-[:FOLLOWED_BY*{min_length}..{max_length}]->(end:Event)
        WHERE start.session_id = $session_id AND end.session_id = $session_id
        RETURN [node in nodes(path) | {{
            event_id: node.event_id,
            type: node.type,
            timestamp: node.timestamp,
            properties: node.properties
        }}] as sequence,
        length(path) as sequence_length
        ORDER BY sequence_length DESC
        """

    @staticmethod
    def find_user_journey_query(user_id: str) -> str:
        """
        Build query to find user journey.

        Args:
            user_id: User identifier

        Returns:
            Cypher query string
        """
        return """
        MATCH (u:User {user_id: $user_id})-[:PERFORMED]->(e:Event)
        RETURN e
        ORDER BY e.timestamp ASC
        """

    @staticmethod
    def find_correlated_patterns_query(
        pattern_id: str, min_correlation: float = 0.5
    ) -> str:
        """
        Build query to find correlated patterns.

        Args:
            pattern_id: Pattern identifier
            min_correlation: Minimum correlation score

        Returns:
            Cypher query string
        """
        return """
        MATCH (p1:Pattern {pattern_id: $pattern_id})-[r:CORRELATES_WITH]-(p2:Pattern)
        WHERE r.correlation_score >= $min_correlation
        RETURN p2, r.correlation_score as correlation
        ORDER BY correlation DESC
        """

    @staticmethod
    def find_anomalous_patterns_query(threshold: float = 0.8) -> str:
        """
        Build query to find anomalous patterns.

        Args:
            threshold: Anomaly score threshold

        Returns:
            Cypher query string
        """
        return """
        MATCH (p:Pattern)
        WHERE p.anomaly_score >= $threshold
        RETURN p
        ORDER BY p.anomaly_score DESC
        """

    @staticmethod
    def find_common_paths_query(
        start_event_type: str, end_event_type: str, max_length: int = 5
    ) -> str:
        """
        Build query to find common paths between event types.

        Args:
            start_event_type: Starting event type
            end_event_type: Ending event type
            max_length: Maximum path length

        Returns:
            Cypher query string
        """
        return f"""
        MATCH path = (start:Event {{type: $start_type}})-[:FOLLOWED_BY*1..{max_length}]->(end:Event {{type: $end_type}})
        WITH path, count(*) as frequency
        WHERE frequency > 1
        RETURN [node in nodes(path) | node.type] as path_types, frequency
        ORDER BY frequency DESC
        LIMIT 10
        """

    @staticmethod
    def find_users_by_pattern_query(pattern_id: str) -> str:
        """
        Build query to find users who performed events matching a pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Cypher query string
        """
        return """
        MATCH (p:Pattern {pattern_id: $pattern_id})-[:CONTAINS]->(e:Event)<-[:PERFORMED]-(u:User)
        RETURN DISTINCT u.user_id as user_id, count(e) as event_count
        ORDER BY event_count DESC
        """

    @staticmethod
    def find_pattern_frequency_query(
        pattern_id: str, time_window_hours: Optional[int] = None
    ) -> str:
        """
        Build query to find pattern frequency within a time window.

        Args:
            pattern_id: Pattern identifier
            time_window_hours: Optional time window in hours

        Returns:
            Cypher query string
        """
        if time_window_hours:
            time_threshold = f"timestamp() - ({time_window_hours} * 3600 * 1000)"
            return f"""
            MATCH (p:Pattern {{pattern_id: $pattern_id}})-[:CONTAINS]->(e:Event)
            WHERE e.timestamp >= {time_threshold}
            RETURN count(e) as frequency
            """
        else:
            return """
            MATCH (p:Pattern {pattern_id: $pattern_id})-[:CONTAINS]->(e:Event)
            RETURN count(e) as frequency
            """
