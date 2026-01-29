"""
inputless-graph - graph_rag_engine.py

Graph RAG engine for LLM-powered insights from graph data.
"""

from typing import List, Dict, Any, Optional
try:
    # LangChain 0.3.0+ imports
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    # Fallback for older LangChain versions
    try:
        from langchain.chat_models import ChatOpenAI, ChatAnthropic
        from langchain.prompts import ChatPromptTemplate
        from langchain.schema import HumanMessage, SystemMessage
    except ImportError:
        # If neither works, raise with helpful message
        raise ImportError(
            "LangChain packages not found. Please install: "
            "pip install langchain langchain-openai langchain-anthropic"
        )
import json
import logging

logger = logging.getLogger(__name__)


class GraphRAGEngine:
    """
    Graph RAG engine for extracting insights from graph data using LLMs.

    Combines graph traversal with LLM reasoning for intelligent insights.
    """

    def __init__(
        self,
        neo4j_repo,
        llm_provider: str = "openai",
        model_name: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """
        Initialize Graph RAG engine.

        Args:
            neo4j_repo: Neo4jRepository instance
            llm_provider: LLM provider ("openai" or "anthropic")
            model_name: Model name (e.g., "gpt-4", "claude-3-opus")
            api_key: API key (if None, uses environment variable)
            temperature: LLM temperature (0.0-1.0)
        """
        self.neo4j_repo = neo4j_repo
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.llm = self._initialize_llm(api_key, temperature)

    def _initialize_llm(self, api_key: Optional[str], temperature: float):
        """
        Initialize LLM based on provider.

        Args:
            api_key: API key (if None, uses environment variable)
            temperature: LLM temperature (0.0-1.0)

        Returns:
            Initialized LLM instance

        Raises:
            ValueError: If provider is unsupported or configuration is invalid
            ImportError: If required LangChain packages are not installed
        """
        try:
            if self.llm_provider == "openai":
                # Try new API first (LangChain 0.3.0+)
                try:
                    return ChatOpenAI(
                        model_name=self.model_name,
                        openai_api_key=api_key,
                        temperature=temperature,
                    )
                except TypeError:
                    # Fallback for older API
                    return ChatOpenAI(
                        model=self.model_name,
                        openai_api_key=api_key,
                        temperature=temperature,
                    )
            elif self.llm_provider == "anthropic":
                # Try new API first (LangChain 0.3.0+)
                try:
                    return ChatAnthropic(
                        model=self.model_name,
                        anthropic_api_key=api_key,
                        temperature=temperature,
                    )
                except TypeError:
                    # Fallback for older API
                    return ChatAnthropic(
                        model_name=self.model_name,
                        anthropic_api_key=api_key,
                        temperature=temperature,
                    )
            else:
                raise ValueError(
                    f"Unsupported LLM provider: '{self.llm_provider}'. "
                    f"Supported providers: 'openai', 'anthropic'"
                )
        except ImportError as e:
            error_msg = (
                f"Failed to import LangChain modules for provider '{self.llm_provider}'. "
                f"Please install required packages: "
                f"pip install langchain-openai langchain-anthropic. "
                f"Original error: {str(e)}"
            )
            logger.error(error_msg)
            raise ImportError(error_msg) from e

    def extract_insights_from_graph(
        self,
        query: str,
        context_limit: int = 50,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract insights from graph using Graph RAG.

        Process:
        1. Find relevant graph nodes based on query
        2. Build context document from graph structure
        3. Use LLM to extract insights from context

        Args:
            query: Natural language query
            context_limit: Maximum number of nodes to include
            session_id: Optional session filter

        Returns:
            Dictionary with insights, confidence, and evidence
        """
        # Step 1: Find relevant nodes
        relevant_nodes = self._find_relevant_nodes(query, context_limit, session_id)

        # Step 2: Build context document
        context_document = self._build_context_document(relevant_nodes)

        # Step 3: Generate insights using LLM
        insights = self._generate_insights(query, context_document)

        return {
            "insights": insights.get("insights", []),
            "confidence": insights.get("confidence", 0.0),
            "supporting_evidence": relevant_nodes[:10],  # Top 10 nodes
            "query": query,
        }

    def _find_relevant_nodes(
        self, query: str, limit: int, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find relevant graph nodes based on query.

        Args:
            query: Natural language query
            limit: Maximum number of nodes to return
            session_id: Optional session filter

        Returns:
            List of relevant node dictionaries
        """
        # Use Cypher to find nodes matching query keywords
        # This is a simplified version - in production, use vector search or semantic matching

        if session_id:
            cypher_query = """
            MATCH (e:Event {session_id: $session_id})
            WHERE e.type CONTAINS $query OR 
                  any(prop in keys(e.properties) WHERE toString(e.properties[prop]) CONTAINS $query)
            RETURN e
            ORDER BY e.timestamp DESC
            LIMIT $limit
            """
        else:
            cypher_query = """
            MATCH (e:Event)
            WHERE e.type CONTAINS $query OR 
                  any(prop in keys(e.properties) WHERE toString(e.properties[prop]) CONTAINS $query)
            RETURN e
            ORDER BY e.timestamp DESC
            LIMIT $limit
            """

        try:
            results = self.neo4j_repo.execute_cypher(
                cypher_query, {"query": query, "limit": limit, "session_id": session_id}
            )

            return [
                {
                    "event_id": r["e"].get("event_id"),
                    "type": r["e"].get("type"),
                    "timestamp": r["e"].get("timestamp"),
                    "properties": r["e"].get("properties", {}),
                }
                for r in results
                if "e" in r
            ]
        except Exception as e:
            logger.error(f"Error finding relevant nodes: {e}")
            return []

    def _build_context_document(self, nodes: List[Dict[str, Any]]) -> str:
        """
        Build context document from graph nodes.

        Args:
            nodes: List of node dictionaries

        Returns:
            Formatted context document string
        """
        if not nodes:
            return "No relevant graph data found."

        context_parts = []

        for node in nodes:
            context_parts.append(
                f"Event: {node.get('type', 'Unknown')} "
                f"(ID: {node.get('event_id', 'Unknown')}, "
                f"Time: {node.get('timestamp', 'Unknown')}, "
                f"Properties: {node.get('properties', {})})"
            )

        return "\n".join(context_parts)

    def _generate_insights(self, query: str, context: str) -> Dict[str, Any]:
        """
        Generate insights using LLM.

        Args:
            query: Natural language query
            context: Graph context document

        Returns:
            Dictionary with insights, confidence, and recommendations
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="""You are an expert behavioral analyst. 
                Analyze the provided graph data and extract meaningful insights.
                Return your response as JSON with:
                - insights: list of key insights
                - confidence: confidence score (0.0-1.0)
                - recommendations: list of actionable recommendations"""
            ),
            HumanMessage(
                content=f"""
                Query: {query}
                
                Graph Context:
                {context}
                
                Please analyze this graph data and provide insights in JSON format.
                """
            ),
        ])

        try:
            response = self.llm.invoke(prompt.format_messages())

            # Parse LLM response (assuming JSON format)
            content = response.content if hasattr(response, "content") else str(response)

            # Extract JSON from response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            error_msg = (
                f"Failed to parse LLM response as JSON. "
                f"Response content: {content[:200]}... "
                f"Error: {str(e)}"
            )
            logger.warning(error_msg)
            # Fallback: return structured response
            return {
                "insights": [content[:500] if content else "No insights generated"],
                "confidence": 0.7,
                "recommendations": [],
            }
        except Exception as e:
            error_msg = (
                f"Error generating insights from graph data. "
                f"Query: {query[:100]}... "
                f"Error: {str(e)}"
            )
            logger.error(error_msg)
            return {
                "insights": [f"Error generating insights: {str(e)}"],
                "confidence": 0.0,
                "recommendations": [],
            }

    def analyze_patterns(
        self, patterns: List[Dict[str, Any]], prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze patterns using LLM.

        Args:
            patterns: List of pattern dictionaries
            prompt: Optional custom prompt

        Returns:
            Analysis results with analysis text and pattern count
        """
        default_prompt = "Explain the behavioral significance of these event sequences"
        analysis_prompt = prompt or default_prompt

        pattern_text = "\n".join([
            f"Pattern {i+1}: {p.get('event_types', [])} - {p.get('sequence', [])}"
            for i, p in enumerate(patterns)
        ])

        messages = [
            SystemMessage(content="You are a behavioral pattern analyst."),
            HumanMessage(content=f"{analysis_prompt}\n\nPatterns:\n{pattern_text}"),
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)

            return {
                "analysis": content,
                "patterns_analyzed": len(patterns),
            }
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {
                "analysis": f"Error analyzing patterns: {str(e)}",
                "patterns_analyzed": len(patterns),
            }
