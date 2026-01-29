"""
inputless-graph - nl_query_agent.py

Natural language query agent for graph database.
"""

from typing import Dict, Any, Optional, List
try:
    # LangChain 0.3.0+ imports
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    # Fallback for older LangChain versions
    try:
        from langchain.chat_models import ChatOpenAI, ChatAnthropic
        from langchain.prompts import ChatPromptTemplate
        from langchain.schema import SystemMessage, HumanMessage
    except ImportError:
        # If neither works, raise with helpful message
        raise ImportError(
            "LangChain packages not found. Please install: "
            "pip install langchain langchain-openai langchain-anthropic"
        )
import json
import re
import logging

logger = logging.getLogger(__name__)


class NLQueryAgent:
    """
    Natural language query agent that translates queries to Cypher.

    Allows users to query graph data using plain English.
    """

    def __init__(
        self,
        neo4j_repo,
        llm_provider: str = "openai",
        model_name: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 0.3,
    ):
        """
        Initialize NL Query Agent.

        Args:
            neo4j_repo: Neo4jRepository instance
            llm_provider: LLM provider ("openai" or "anthropic")
            model_name: Model name
            api_key: API key (if None, uses environment variable)
            temperature: LLM temperature (lower for more deterministic queries)
        """
        self.neo4j_repo = neo4j_repo
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.llm = self._initialize_llm(llm_provider, model_name, api_key, temperature)

    def _initialize_llm(
        self, provider: str, model: str, api_key: Optional[str], temperature: float
    ):
        """
        Initialize LLM based on provider.

        Args:
            provider: LLM provider name
            model: Model name
            api_key: API key (if None, uses environment variable)
            temperature: LLM temperature (0.0-1.0)

        Returns:
            Initialized LLM instance

        Raises:
            ValueError: If provider is unsupported
            ImportError: If required LangChain packages are not installed
        """
        try:
            if provider == "openai":
                # Try new API first (LangChain 0.3.0+)
                try:
                    return ChatOpenAI(
                        model_name=model, openai_api_key=api_key, temperature=temperature
                    )
                except TypeError:
                    # Fallback for older API
                    return ChatOpenAI(
                        model=model, openai_api_key=api_key, temperature=temperature
                    )
            elif provider == "anthropic":
                # Try new API first (LangChain 0.3.0+)
                try:
                    return ChatAnthropic(
                        model=model, anthropic_api_key=api_key, temperature=temperature
                    )
                except TypeError:
                    # Fallback for older API
                    return ChatAnthropic(
                        model_name=model, anthropic_api_key=api_key, temperature=temperature
                    )
            else:
                raise ValueError(
                    f"Unsupported provider: '{provider}'. "
                    f"Supported providers: 'openai', 'anthropic'"
                )
        except ImportError as e:
            error_msg = (
                f"Failed to import LangChain modules for provider '{provider}'. "
                f"Please install required packages: "
                f"pip install langchain-openai langchain-anthropic. "
                f"Original error: {str(e)}"
            )
            logger.error(error_msg)
            raise ImportError(error_msg) from e

    def query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Execute natural language query on graph.

        Process:
        1. Translate NL query to Cypher
        2. Execute Cypher query
        3. Format results
        4. Generate explanation

        Args:
            natural_language_query: Query in plain English

        Returns:
            Dictionary with results, query, and explanation
        """
        # Step 1: Translate to Cypher
        cypher_query = self._translate_to_cypher(natural_language_query)

        # Step 2: Execute query
        try:
            results = self.neo4j_repo.execute_cypher(cypher_query)
        except Exception as e:
            error_msg = (
                f"Error executing Cypher query. "
                f"Query: {cypher_query[:200]}... "
                f"Error: {str(e)}"
            )
            logger.error(error_msg)
            return {
                "error": str(e),
                "cypher_query": cypher_query,
                "original_query": natural_language_query,
                "results": [],
                "result_count": 0,
            }

        # Step 3: Format results
        formatted_results = self._format_results(results)

        # Step 4: Generate explanation
        explanation = self._generate_explanation(
            natural_language_query, cypher_query, formatted_results
        )

        return {
            "results": formatted_results,
            "cypher_query": cypher_query,
            "query_explanation": explanation,
            "result_count": len(formatted_results),
        }

    def _translate_to_cypher(self, nl_query: str) -> str:
        """
        Translate natural language query to Cypher.

        Args:
            nl_query: Natural language query

        Returns:
            Cypher query string
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="""You are a Cypher query expert. 
                Translate natural language queries to Neo4j Cypher queries.
                
                Graph Schema:
                - Nodes: Event (event_id, type, timestamp, session_id, user_id, properties)
                - Nodes: User (user_id, properties)
                - Nodes: Pattern (pattern_id, event_types, sequence, frequency, confidence)
                - Relationships: FOLLOWED_BY (Event -> Event)
                - Relationships: PERFORMED (User -> Event)
                - Relationships: CONTAINS (Pattern -> Event)
                - Relationships: SIMILAR_TO (Event -> Event)
                - Relationships: CORRELATES_WITH (Pattern -> Pattern)
                
                Return ONLY the Cypher query, no explanation."""
            ),
            HumanMessage(content=f"Translate this query to Cypher: {nl_query}"),
        ])

        try:
            response = self.llm.invoke(prompt.format_messages())
            cypher = (
                response.content if hasattr(response, "content") else str(response)
            )
            cypher = cypher.strip()

            # Clean up response (remove markdown code blocks if present)
            if "```cypher" in cypher:
                cypher = re.sub(r"```cypher\n?", "", cypher)
            if "```" in cypher:
                cypher = re.sub(r"```\n?", "", cypher)

            return cypher.strip()
        except Exception as e:
            error_msg = (
                f"Error translating natural language query to Cypher. "
                f"Query: {nl_query[:100]}... "
                f"Error: {str(e)}"
            )
            logger.error(error_msg)
            # Fallback: return a simple query
            logger.warning("Using fallback Cypher query due to translation error")
            return "MATCH (e:Event) RETURN e LIMIT 10"

    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format query results for readability.

        Args:
            results: Raw query results from Neo4j

        Returns:
            Formatted results
        """
        formatted = []
        for result in results:
            formatted_item = {}
            for key, value in result.items():
                # Handle Neo4j node objects
                if hasattr(value, "items"):
                    formatted_item[key] = dict(value)
                elif hasattr(value, "__dict__"):
                    # Handle other Neo4j objects
                    formatted_item[key] = str(value)
                else:
                    formatted_item[key] = value
            formatted.append(formatted_item)
        return formatted

    def _generate_explanation(
        self,
        nl_query: str,
        cypher_query: str,
        results: List[Dict[str, Any]],
    ) -> str:
        """
        Generate natural language explanation of query results.

        Args:
            nl_query: Original natural language query
            cypher_query: Generated Cypher query
            results: Query results

        Returns:
            Natural language explanation
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a data analyst explaining query results."),
            HumanMessage(
                content=f"""
                Original Query: {nl_query}
                Cypher Query: {cypher_query}
                Results: {json.dumps(results[:10], indent=2)}  # Limit to first 10
                
                Provide a clear explanation of what these results mean.
                """
            ),
        ])

        try:
            response = self.llm.invoke(prompt.format_messages())
            return (
                response.content if hasattr(response, "content") else str(response)
            )
        except Exception as e:
            error_msg = (
                f"Error generating explanation for query results. "
                f"Query: {nl_query[:100]}... "
                f"Results count: {len(results)} "
                f"Error: {str(e)}"
            )
            logger.error(error_msg)
            return f"Found {len(results)} results for query: {nl_query}"
