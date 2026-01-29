"""
Example usage of the graph module.

This file demonstrates how to use the graph module to store events,
query patterns, and extract insights using Graph RAG.
"""

from typing import List, Dict, Any
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from neo4j_repository import Neo4jRepository, Neo4jConfig
from graph_rag_engine import GraphRAGEngine
from nl_query_agent import NLQueryAgent
from insight_generator import InsightGenerator


def example_basic_operations():
    """Example: Basic Neo4j operations"""
    print("=" * 60)
    print("Example 1: Basic Neo4j Operations")
    print("=" * 60)

    # Initialize repository
    config = Neo4jConfig(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password",
    )

    try:
        repo = Neo4jRepository(config)

        # Create user node
        user_id = repo.create_user_node("user-123", {"name": "John Doe"})
        print(f"Created user node: {user_id}")

        # Create event nodes
        events = [
            {
                "event_id": "event-1",
                "type": "ui.click",
                "timestamp": 1000,
                "session_id": "session-1",
                "user_id": "user-123",
                "properties": {"element": "button", "text": "Submit"},
            },
            {
                "event_id": "event-2",
                "type": "form.submit",
                "timestamp": 2000,
                "session_id": "session-1",
                "user_id": "user-123",
                "properties": {"form_id": "login-form"},
            },
        ]

        for event in events:
            event_node_id = repo.create_event_node(event)
            print(f"Created event node: {event_node_id}")
            repo.link_user_to_event(event["user_id"], event["event_id"])

        # Connect events
        repo.connect_events(
            "event-1",
            "event-2",
            "FOLLOWED_BY",
            {"time_delta": 1000},
        )
        print("Connected events with FOLLOWED_BY relationship")

        # Find event sequences
        sequences = repo.find_event_sequences("session-1", min_length=2, max_length=5)
        print(f"\nFound {len(sequences)} event sequences")
        for i, seq in enumerate(sequences[:3], 1):
            print(f"  Sequence {i}: {len(seq)} events")

        # Find user journey
        journey = repo.find_user_journey("user-123")
        print(f"\nUser journey: {len(journey)} events")

        repo.close()
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure Neo4j is running and accessible")


def example_graph_rag():
    """Example: Graph RAG for insights"""
    print("\n" + "=" * 60)
    print("Example 2: Graph RAG for Insights")
    print("=" * 60)

    try:
        # Initialize repository and RAG engine
        repo = Neo4jRepository()
        rag_engine = GraphRAGEngine(
            neo4j_repo=repo,
            llm_provider="openai",
            model_name="gpt-4",
        )

        # Extract insights
        insights = rag_engine.extract_insights_from_graph(
            query="What are the main barriers preventing users from completing purchase?",
            context_limit=50,
        )

        print(f"\nInsights (confidence: {insights['confidence']:.2f}):")
        for i, insight in enumerate(insights["insights"], 1):
            print(f"  {i}. {insight}")

        repo.close()
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure OpenAI API key is set and Neo4j is running")


def example_nl_queries():
    """Example: Natural language queries"""
    print("\n" + "=" * 60)
    print("Example 3: Natural Language Queries")
    print("=" * 60)

    try:
        # Initialize repository and NL agent
        repo = Neo4jRepository()
        nl_agent = NLQueryAgent(
            neo4j_repo=repo,
            llm_provider="openai",
        )

        # Query in natural language
        result = nl_agent.query("Show me users who are about to abandon their cart")

        print(f"\nQuery: {result.get('original_query', 'N/A')}")
        print(f"Cypher: {result.get('cypher_query', 'N/A')}")
        print(f"Results: {result.get('result_count', 0)} found")
        print(f"\nExplanation:\n{result.get('query_explanation', 'N/A')}")

        repo.close()
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure OpenAI API key is set and Neo4j is running")


def example_insight_generation():
    """Example: Insight generation from documents"""
    print("\n" + "=" * 60)
    print("Example 4: Insight Generation")
    print("=" * 60)

    try:
        # Initialize components
        repo = Neo4jRepository()
        rag_engine = GraphRAGEngine(neo4j_repo=repo, llm_provider="openai")
        insight_gen = InsightGenerator(rag_engine)

        # Analyze behavioral document
        user_document = {
            "user_id": "user_123",
            "session_context": "e-commerce checkout",
            "event_sequence": [
                {"action": "view_product", "time": "10:00"},
                {"action": "add_to_cart", "time": "10:02"},
                {"action": "view_cart", "time": "10:03"},
                {"action": "initiate_checkout", "time": "10:05"},
                {"action": "abandon_cart", "time": "10:08"},
            ],
        }

        insights = insight_gen.extract_insights(user_document)

        print(f"\nRisk Score: {insights.get('risk_score', 0):.2f}")
        print(f"Intervention Needed: {insights.get('intervention_needed', False)}")

        print("\nKey Insights:")
        for i, insight in enumerate(insights.get("key_insights", []), 1):
            print(f"  {i}. {insight}")

        print("\nRecommendations:")
        for i, rec in enumerate(insights.get("recommendations", []), 1):
            print(f"  {i}. {rec}")

        repo.close()
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure OpenAI API key is set and Neo4j is running")


def main():
    """Main entry point for running examples"""
    print("Graph Module Examples")
    print("=" * 60)

    # Run examples
    example_basic_operations()
    # Uncomment when Neo4j and API keys are configured:
    # example_graph_rag()
    # example_nl_queries()
    # example_insight_generation()


if __name__ == "__main__":
    main()

