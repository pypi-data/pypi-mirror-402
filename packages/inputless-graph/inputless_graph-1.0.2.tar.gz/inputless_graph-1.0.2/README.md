# inputless-graph

Neo4j graph database integration for behavioral analytics.

## Purpose

Provides graph database functionality for storing and querying behavioral event relationships, enabling complex pattern discovery and correlation analysis.

## Features

- **Event Sequence Analysis**: Track event sequences through graph traversal
- **Pattern Correlation**: Find correlated events and patterns
- **User Journey Mapping**: Map complete user journeys
- **Graph Algorithms**: Built-in graph algorithms for analysis
- **Anomaly Detection**: Graph-based anomaly detection
- **Graph RAG (Retrieval Augmented Generation)**: LLM-powered insight extraction from graph documents
- **Natural Language Query Interface**: Query graph data using plain English
- **Semantic Insights Generation**: AI extracts meaningful insights from behavioral patterns

## Installation

```bash
pip install inputless-graph
```

## Dependencies

- `neo4j` - Neo4j Python driver
- `py2neo` - Neo4j OGM (optional)
- `pydantic` - Data validation
- `langchain` - LLM orchestration
- `openai` or `anthropic` - LLM APIs
- `tiktoken` - Token counting
- `sentence-transformers` - Embeddings (optional, for future semantic search features)

## Installation

```bash
# Using Poetry
poetry add inputless-graph

# Or using pip
pip install inputless-graph
```

## Quick Start

```python
from inputless_graph import Neo4jRepository, Neo4jConfig, GraphRAGEngine, NLQueryAgent, InsightGenerator

# Initialize repository
config = Neo4jConfig(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="neo4j"  # Optional
)

repo = Neo4jRepository(config)

# Store events
event = {
    "event_id": "event-123",
    "type": "ui.click",
    "timestamp": 1699123456000,
    "session_id": "session-456",
    "user_id": "user-789",
    "properties": {"element": "button", "page": "/checkout"}
}

node_id = repo.create_event_node(event)
print(f"Created event node: {node_id}")

# Connect events
repo.connect_events("event-123", "event-124", "FOLLOWED_BY", {"time_delta": 1000})

# Find event sequences
sequences = repo.find_event_sequences("session-456", min_length=2, max_length=10)
print(f"Found {len(sequences)} event sequences")

# Find user journey
journey = repo.find_user_journey("user-789")
print(f"User journey: {len(journey)} events")

# Clean up
repo.close()
```

## Module Structure

This module contains:
- `neo4j_repository.py` - Neo4j database operations
- `graph_models.py` - Graph data models
- `graph_queries.py` - Cypher query builders
- `graph_analyzer.py` - Graph analysis tools
- `query_optimizer.py` - Query optimization
- `graph_rag_engine.py` - Graph RAG for LLM-powered insights
- `nl_query_agent.py` - Natural language query interface
- `insight_generator.py` - AI-powered insight extraction from graph documents

## Graph Schema

### Nodes
- `Event` - Behavioral events
- `User` - Users
- `Pattern` - Discovered patterns
- `Insight` - Generated insights

### Relationships
- `PERFORMED` - User → Event
- `FOLLOWED_BY` - Event → Event
- `SIMILAR_TO` - Event → Event
- `CONTAINS` - Pattern → Event
- `CORRELATES_WITH` - Pattern → Pattern

## Usage Examples

### Basic Graph Operations

```python
from inputless_graph import Neo4jRepository, Neo4jConfig

# Initialize repository
config = Neo4jConfig(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)
repo = Neo4jRepository(config)

# Create user node
user_id = repo.create_user_node("user-123", {"name": "John Doe", "email": "john@example.com"})

# Create event nodes
events = [
    {
        "event_id": "event-1",
        "type": "ui.click",
        "timestamp": 1699123456000,
        "session_id": "session-1",
        "user_id": "user-123",
        "properties": {"element": "button", "text": "Add to Cart"}
    },
    {
        "event_id": "event-2",
        "type": "form.submit",
        "timestamp": 1699123457000,
        "session_id": "session-1",
        "user_id": "user-123",
        "properties": {"form_id": "checkout-form"}
    }
]

for event in events:
    node_id = repo.create_event_node(event)
    repo.link_user_to_event(event["user_id"], event["event_id"])

# Connect events with relationship
repo.connect_events(
    "event-1",
    "event-2",
    "FOLLOWED_BY",
    {"time_delta": 1000, "sequence_order": 1}
)

# Find event sequences
sequences = repo.find_event_sequences("session-1", min_length=2, max_length=5)
for seq in sequences:
    print(f"Sequence with {len(seq)} events")

# Find user journey
journey = repo.find_user_journey("user-123")
print(f"User journey contains {len(journey)} events")

# Find similar events
similar = repo.find_similar_events("event-1", similarity_threshold=0.7)
print(f"Found {len(similar)} similar events")

# Create pattern node
pattern_data = {
    "event_types": ["ui.click", "form.submit"],
    "sequence": ["event-1", "event-2"],
    "frequency": 10,
    "confidence": 0.85,
    "properties": {"category": "conversion"}
}
pattern_id = repo.create_pattern_node("pattern-123", pattern_data)

# Execute custom Cypher query
results = repo.execute_cypher(
    "MATCH (e:Event) RETURN count(e) as total_events",
    {}
)
print(f"Total events: {results[0]['total_events']}")

repo.close()
```

### Graph RAG for LLM-Powered Insights

```python
from inputless_graph import Neo4jRepository, GraphRAGEngine
import os

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# Initialize Graph RAG engine
repo = Neo4jRepository()
rag_engine = GraphRAGEngine(
    neo4j_repo=repo,
    llm_provider="openai",  # or "anthropic"
    model_name="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY"),  # Optional, uses env var if None
    temperature=0.7
)

# Extract insights from graph
insights = rag_engine.extract_insights_from_graph(
    query="What are the main barriers preventing users from completing purchase?",
    context_limit=50,  # Number of relevant graph nodes to include
    session_id="session-1"  # Optional: filter by session
)

print(f"Confidence: {insights['confidence']:.2f}")
print("\nInsights:")
for i, insight in enumerate(insights["insights"], 1):
    print(f"  {i}. {insight}")

print(f"\nSupporting Evidence: {len(insights['supporting_evidence'])} nodes")

# Analyze patterns with LLM
patterns = [
    {"pattern_id": "p1", "event_types": ["click", "submit"], "frequency": 100},
    {"pattern_id": "p2", "event_types": ["view", "scroll"], "frequency": 50}
]

pattern_analysis = rag_engine.analyze_patterns(
    patterns=patterns,
    prompt="Explain the behavioral significance of these patterns"
)

print("\nPattern Analysis:")
print(pattern_analysis)

repo.close()
```

### Natural Language Query Interface

```python
from inputless_graph import Neo4jRepository, NLQueryAgent
import os

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# Initialize NL Query Agent
repo = Neo4jRepository()
nl_agent = NLQueryAgent(
    neo4j_repo=repo,
    llm_provider="openai",  # or "anthropic"
    model_name="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY"),  # Optional
    temperature=0.3  # Lower temperature for more deterministic queries
)

# Query in natural language
result = nl_agent.query("Show me users who are about to abandon their cart")

# The agent automatically:
# 1. Translates natural language to Cypher query
# 2. Executes the query on Neo4j
# 3. Formats the results
# 4. Generates a natural language explanation

print(f"Cypher Query: {result['cypher_query']}")
print(f"Results Found: {result['result_count']}")
print(f"\nExplanation:\n{result['query_explanation']}")

# Example output:
# Cypher Query: MATCH (u:User)-[:PERFORMED]->(e:Event)
#               WHERE e.type = 'cart.abandon' 
#               RETURN u.user_id, count(e) as abandon_count
# Results Found: 124
# Explanation: Found 124 users with cart abandonment events...

# More examples
queries = [
    "Find all events in the last hour",
    "Show me the most common event sequences",
    "Which users have the longest sessions?",
    "Find patterns that correlate with high conversion"
]

for query in queries:
    result = nl_agent.query(query)
    print(f"\nQuery: {query}")
    print(f"Results: {result['result_count']}")

repo.close()
```

### Document-Based Insight Extraction

```python
from inputless_graph import Neo4jRepository, GraphRAGEngine, InsightGenerator
import os

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# Initialize components
repo = Neo4jRepository()
rag_engine = GraphRAGEngine(neo4j_repo=repo, llm_provider="openai")
insight_gen = InsightGenerator(rag_engine)

# Analyze behavioral documents (event sequences as documents)
user_document = {
    "user_id": "user_123",
    "session_context": "e-commerce checkout",
    "event_sequence": [
        {"action": "view_product", "time": "10:00"},
        {"action": "add_to_cart", "time": "10:02"},
        {"action": "view_cart", "time": "10:03"},
        {"action": "initiate_checkout", "time": "10:05"},
        {"action": "abandon_cart", "time": "10:08"}
    ]
}

insights = insight_gen.extract_insights(user_document)

print(f"Risk Score: {insights['risk_score']:.2f}")
print(f"Intervention Needed: {insights['intervention_needed']}")

print("\nKey Insights:")
for i, insight in enumerate(insights["key_insights"], 1):
    print(f"  {i}. {insight}")

print("\nRecommendations:")
for i, rec in enumerate(insights["recommendations"], 1):
    print(f"  {i}. {rec}")

# Example output:
# Risk Score: 0.65
# Intervention Needed: True
# 
# Key Insights:
#   1. User showed high purchase intent (quick progression through funnel)
#   2. Abandonment at payment stage suggests price/trust concerns
#   3. 3-minute hesitation indicates decision-making process
# 
# Recommendations:
#   1. Offer guest checkout option
#   2. Provide trust badges and security indicators
#   3. Show limited-time discount or free shipping

repo.close()
```

### Using Graph Query Builders

```python
from inputless_graph import GraphQueries

# Build Cypher queries programmatically
query = GraphQueries.find_event_sequences_query(
    session_id="session-1",
    min_length=2,
    max_length=10
)

# Find user journey query
journey_query = GraphQueries.find_user_journey_query(user_id="user-123")

# Find correlated patterns
correlation_query = GraphQueries.find_correlated_patterns_query(
    pattern_id="pattern-123",
    min_correlation=0.5
)

# Find anomalous patterns
anomaly_query = GraphQueries.find_anomalous_patterns_query(threshold=0.8)

# Find common paths between event types
paths_query = GraphQueries.find_common_paths_query(
    start_event_type="ui.click",
    end_event_type="form.submit",
    max_length=5
)

# Find pattern frequency
frequency_query = GraphQueries.find_pattern_frequency_query(
    pattern_id="pattern-123",
    time_window_hours=24  # Optional: filter by time window
)

# Execute queries using repository
results = repo.execute_cypher(query, {"session_id": "session-1"})
```

## API Reference

### Core Classes

#### `Neo4jRepository`
Main repository for Neo4j database operations.

```python
from inputless_graph import Neo4jRepository, Neo4jConfig

config = Neo4jConfig(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="neo4j",  # Optional
    max_connection_lifetime=3600,
    max_connection_pool_size=50
)
repo = Neo4jRepository(config)
```

**Key Methods:**
- `create_event_node(event: Dict) -> Optional[int]` - Create event node
- `create_user_node(user_id: str, properties: Dict) -> Optional[int]` - Create user node
- `create_pattern_node(pattern_id: str, pattern_data: Dict) -> Optional[int]` - Create pattern node
- `connect_events(event1_id, event2_id, relationship_type, properties)` - Connect events
- `link_user_to_event(user_id, event_id)` - Link user to event
- `find_event_sequences(session_id, min_length, max_length)` - Find event sequences
- `find_user_journey(user_id)` - Find user journey
- `find_similar_events(event_id, similarity_threshold)` - Find similar events
- `execute_cypher(query, parameters)` - Execute raw Cypher query
- `close()` - Close connection

#### `GraphRAGEngine`
LLM-powered insight extraction from graph data.

```python
from inputless_graph import GraphRAGEngine

rag_engine = GraphRAGEngine(
    neo4j_repo=repo,
    llm_provider="openai",  # or "anthropic"
    model_name="gpt-4",
    api_key="your-api-key",  # Optional, uses env var if None
    temperature=0.7
)
```

**Key Methods:**
- `extract_insights_from_graph(query, context_limit, session_id)` - Extract insights
- `analyze_patterns(patterns, prompt)` - Analyze patterns with LLM

#### `NLQueryAgent`
Natural language query interface for graph database.

```python
from inputless_graph import NLQueryAgent

nl_agent = NLQueryAgent(
    neo4j_repo=repo,
    llm_provider="openai",
    model_name="gpt-4",
    temperature=0.3  # Lower for more deterministic queries
)
```

**Key Methods:**
- `query(natural_language_query: str)` - Execute natural language query

#### `InsightGenerator`
AI-powered insight extraction from behavioral documents.

```python
from inputless_graph import InsightGenerator

insight_gen = InsightGenerator(rag_engine)
```

**Key Methods:**
- `extract_insights(document: Dict)` - Extract insights from behavioral document

### Data Models

#### `Neo4jConfig`
Configuration for Neo4j connection.

```python
from inputless_graph import Neo4jConfig

config = Neo4jConfig(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="neo4j",
    max_connection_lifetime=3600,
    max_connection_pool_size=50
)
```

#### Pydantic Models
- `EventNode` - Event node model
- `UserNode` - User node model
- `PatternNode` - Pattern node model
- `Relationship` - Relationship model
- `EventSequence` - Event sequence model
- `UserJourney` - User journey model

### Query Builders

#### `GraphQueries`
Static methods for building common Cypher queries.

```python
from inputless_graph import GraphQueries

# All methods are static
query = GraphQueries.find_event_sequences_query(session_id, min_length, max_length)
query = GraphQueries.find_user_journey_query(user_id)
query = GraphQueries.find_correlated_patterns_query(pattern_id, min_correlation)
query = GraphQueries.find_anomalous_patterns_query(threshold)
query = GraphQueries.find_common_paths_query(start_type, end_type, max_length)
query = GraphQueries.find_users_by_pattern_query(pattern_id)
query = GraphQueries.find_pattern_frequency_query(pattern_id, time_window_hours)
```

## Testing

Run the test suite:

```bash
cd packages/python-core/graph
poetry install
poetry run pytest tests/ -v
```

**Test Coverage:**
- ✅ 70 tests passing
- ✅ All core modules tested
- ✅ Mocked Neo4j driver and LLM dependencies
- ✅ Comprehensive error handling tests

## Configuration

### Environment Variables

```bash
# Neo4j Connection (or use Neo4jConfig)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### LLM Provider Support

The module supports both OpenAI and Anthropic LLM providers:

```python
# OpenAI
rag_engine = GraphRAGEngine(
    neo4j_repo=repo,
    llm_provider="openai",
    model_name="gpt-4"
)

# Anthropic
rag_engine = GraphRAGEngine(
    neo4j_repo=repo,
    llm_provider="anthropic",
    model_name="claude-3-opus"
)
```

## Error Handling

All methods include comprehensive error handling:

```python
try:
    repo = Neo4jRepository(config)
    node_id = repo.create_event_node(event)
except ConnectionError as e:
    print(f"Failed to connect to Neo4j: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"Database operation failed: {e}")
finally:
    repo.close()
```

## Performance Considerations

- **Connection Pooling**: Configured via `max_connection_pool_size` in `Neo4jConfig`
- **Query Optimization**: Use `GraphQueries` for optimized Cypher queries
- **Context Limits**: Set `context_limit` in Graph RAG to control LLM token usage
- **Batch Operations**: Use `execute_cypher` for bulk operations

## Exports

```python
from inputless_graph import (
    # Core classes
    Neo4jRepository,
    Neo4jConfig,
    GraphRAGEngine,
    NLQueryAgent,
    InsightGenerator,
    GraphQueries,
    
    # Models
    EventNode,
    UserNode,
    PatternNode,
    Relationship,
    EventSequence,
    UserJourney,
    GraphModels,  # Dict of all models
)
```

## Module Structure

```
src/inputless_graph/
├── __init__.py              # Public API exports
├── neo4j_repository.py      # Neo4j database operations
├── graph_models.py          # Pydantic data models
├── graph_queries.py         # Cypher query builders
├── graph_rag_engine.py      # Graph RAG for LLM insights
├── nl_query_agent.py        # Natural language query agent
├── insight_generator.py      # AI-powered insight extraction
├── example_usage.py         # Usage examples
└── features/                # Optional advanced features
    ├── natural_language_behavior_queries.py
    └── quantum_inspired_processing.py
```

## Development

### Setup

```bash
cd packages/python-core/graph
poetry install
```

### Running Examples

```bash
poetry run python src/inputless_graph/example_usage.py
```

### Running Tests

```bash
poetry run pytest tests/ -v
poetry run pytest tests/ --cov=src --cov-report=html
```

## Distribution

**PyPI package**: `inputless-graph`  
**Version**: 1.0.0  
**Registry**: PyPI  
**License**: MIT

## Contributing

See the main project README for contribution guidelines.

## License

MIT License - see LICENSE file for details.

