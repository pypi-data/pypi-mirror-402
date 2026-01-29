"""
inputless-graph - graph_models.py

Pydantic models for graph data structures.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EventNode(BaseModel):
    """Event node model"""

    event_id: str = Field(..., description="Unique event identifier")
    type: str = Field(..., description="Event type")
    timestamp: int = Field(..., description="Event timestamp (Unix timestamp)")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Additional event properties"
    )


class UserNode(BaseModel):
    """User node model"""

    user_id: str = Field(..., description="Unique user identifier")
    created_at: Optional[int] = Field(
        None, description="User creation timestamp"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Additional user properties"
    )


class PatternNode(BaseModel):
    """Pattern node model"""

    pattern_id: str = Field(..., description="Unique pattern identifier")
    event_types: List[str] = Field(
        ..., description="List of event types in pattern"
    )
    sequence: List[str] = Field(
        ..., description="Sequence of events in pattern"
    )
    frequency: int = Field(
        default=0, description="Pattern frequency (occurrence count)"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Pattern confidence score"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Additional pattern properties"
    )


class Relationship(BaseModel):
    """Relationship model"""

    from_node_id: str = Field(..., description="Source node identifier")
    to_node_id: str = Field(..., description="Target node identifier")
    relationship_type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Relationship properties"
    )


class EventSequence(BaseModel):
    """Event sequence model"""

    sequence_id: str = Field(..., description="Unique sequence identifier")
    events: List[EventNode] = Field(..., description="List of events in sequence")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    length: int = Field(..., ge=1, description="Sequence length")
    timestamp_start: int = Field(..., description="Sequence start timestamp")
    timestamp_end: int = Field(..., description="Sequence end timestamp")


class UserJourney(BaseModel):
    """User journey model"""

    user_id: str = Field(..., description="User identifier")
    events: List[EventNode] = Field(..., description="List of events in journey")
    sessions: List[str] = Field(..., description="List of session IDs")
    total_events: int = Field(..., ge=0, description="Total number of events")
    first_event_time: int = Field(..., description="First event timestamp")
    last_event_time: int = Field(..., description="Last event timestamp")


# GraphModels dict kept for backward compatibility
GraphModels = {
    "EventNode": EventNode,
    "UserNode": UserNode,
    "PatternNode": PatternNode,
    "Relationship": Relationship,
    "EventSequence": EventSequence,
    "UserJourney": UserJourney,
}

__all__ = [
    "EventNode",
    "UserNode",
    "PatternNode",
    "Relationship",
    "EventSequence",
    "UserJourney",
    "GraphModels",
]
