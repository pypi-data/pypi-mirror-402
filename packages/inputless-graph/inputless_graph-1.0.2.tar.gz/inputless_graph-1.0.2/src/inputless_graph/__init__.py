"""
inputless-graph - Main exports

Neo4j graph database integration, Graph RAG engine, and natural language query agent.
"""

from .neo4j_repository import Neo4jRepository, Neo4jConfig
from .graph_models import (
    EventNode,
    UserNode,
    PatternNode,
    Relationship,
    EventSequence,
    UserJourney,
    GraphModels,
)
from .graph_queries import GraphQueries
from .nl_query_agent import NLQueryAgent
from .graph_rag_engine import GraphRAGEngine
from .insight_generator import InsightGenerator

# Feature implementations (see features/ directory for details)
try:
    from .features import NaturalLanguageBehaviorQueryAgent, QuantumInspiredProcessor

    __all__ = [
        # Core classes
        "Neo4jRepository",
        "Neo4jConfig",
        "GraphQueries",
        "NLQueryAgent",
        "GraphRAGEngine",
        "InsightGenerator",
        # Models
        "EventNode",
        "UserNode",
        "PatternNode",
        "Relationship",
        "EventSequence",
        "UserJourney",
        "GraphModels",
        # Features
        "NaturalLanguageBehaviorQueryAgent",
        "QuantumInspiredProcessor",
    ]
except ImportError:
    # Features not yet implemented
    __all__ = [
        # Core classes
        "Neo4jRepository",
        "Neo4jConfig",
        "GraphQueries",
        "NLQueryAgent",
        "GraphRAGEngine",
        "InsightGenerator",
        # Models
        "EventNode",
        "UserNode",
        "PatternNode",
        "Relationship",
        "EventSequence",
        "UserJourney",
        "GraphModels",
    ]

