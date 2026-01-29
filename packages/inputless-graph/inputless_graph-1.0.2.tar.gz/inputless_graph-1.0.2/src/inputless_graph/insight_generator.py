"""
inputless-graph - insight_generator.py

AI-powered insight extraction from behavioral documents.
"""

from typing import Dict, Any, Optional
try:
    # LangChain 0.3.0+ imports
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    # Fallback for older LangChain versions
    try:
        from langchain.prompts import ChatPromptTemplate
        from langchain.schema import SystemMessage, HumanMessage
    except ImportError:
        # If neither works, raise with helpful message
        raise ImportError(
            "LangChain packages not found. Please install: "
            "pip install langchain langchain-openai langchain-anthropic"
        )
import json
import logging

logger = logging.getLogger(__name__)


class InsightGenerator:
    """
    Generate insights from behavioral documents using LLM.

    Analyzes event sequences as documents and extracts meaningful insights.
    """

    def __init__(self, graph_rag_engine):
        """
        Initialize Insight Generator.

        Args:
            graph_rag_engine: GraphRAGEngine instance (provides LLM access)
        """
        self.graph_rag_engine = graph_rag_engine
        self.llm = graph_rag_engine.llm

    def extract_insights(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract insights from behavioral document.

        Args:
            document: Document with user_id, session_context, event_sequence

        Returns:
            Dictionary with insights, recommendations, risk_score, etc.
        """
        # Format document as text
        document_text = self._format_document(document)

        # Generate insights using LLM
        insights = self._generate_insights(document_text)

        return insights

    def _format_document(self, document: Dict[str, Any]) -> str:
        """
        Format document as text for LLM.

        Args:
            document: Document dictionary

        Returns:
            Formatted document text
        """
        parts = [
            f"User ID: {document.get('user_id', 'Unknown')}",
            f"Session Context: {document.get('session_context', 'Unknown')}",
            "\nEvent Sequence:",
        ]

        for i, event in enumerate(document.get("event_sequence", []), 1):
            action = event.get("action", "Unknown")
            time = event.get("time", "Unknown")
            parts.append(f"  {i}. {action} at {time}")

        return "\n".join(parts)

    def _generate_insights(self, document_text: str) -> Dict[str, Any]:
        """
        Generate insights using LLM.

        Args:
            document_text: Formatted document text

        Returns:
            Dictionary with insights, recommendations, risk_score, etc.
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="""You are a behavioral analyst. 
                Analyze user behavior and extract insights.
                Return JSON with:
                - key_insights: list of insights
                - recommendations: list of recommendations
                - risk_score: 0.0-1.0
                - intervention_needed: boolean"""
            ),
            HumanMessage(
                content=f"Analyze this behavioral document:\n\n{document_text}"
            ),
        ])

        try:
            response = self.llm.invoke(prompt.format_messages())
            content = response.content if hasattr(response, "content") else str(response)

            # Parse JSON response
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
            # Fallback
            return {
                "key_insights": [
                    content[:500] if content else "No insights generated from document"
                ],
                "recommendations": [],
                "risk_score": 0.5,
                "intervention_needed": False,
            }
        except Exception as e:
            error_msg = (
                f"Error generating insights from behavioral document. "
                f"Document preview: {document_text[:200]}... "
                f"Error: {str(e)}"
            )
            logger.error(error_msg)
            return {
                "key_insights": [f"Error generating insights: {str(e)}"],
                "recommendations": [],
                "risk_score": 0.0,
                "intervention_needed": False,
            }
