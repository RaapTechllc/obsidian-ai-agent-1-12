"""Pydantic models for smart search system."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Parsed user search query with intent analysis and AI intent."""
    
    original_query: str = Field(..., description="Original user search query")
    intent_type: Literal["search", "find", "discover", "organize", "classify"] = Field(
        default="search", 
        description="Type of intent the query represents"
    )
    entities: list[str] = Field(
        default_factory=list, 
        description="Key entities mentioned in the query"
    )
    context_keywords: list[str] = Field(
        default_factory=list,
        description="Important contextual clues from query"
    )
    search_type: Literal["title", "content", "metadata", "tags", "path"] | None = Field(
        default=None,
        description="What type of search to perform if clear"
    )
    filters: Optional[dict[str, str | bool | list[str] | int | float]] = Field(
        default=None,
        description="Search filters to apply"
    )
    response_format: Literal["minimal", "coincise", "detailed"] = Field(
        default="concise",
        description="Output verbosity for results"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum results to return"
    )
    
    # Planning fields (filled by agent)
    estimated_complexity: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Estimated complexity of search based on query"
    )
    execution_plan: list[str] = Field(
        default_factory=list,
        description="Planned execution steps"
    )


class SearchResult(BaseModel):
    """Enhanced search result with confidence scoring."""
    
    path: str = Field(..., description="Note file path")
    title: str | None = Field(..., description="Note title from frontmatter")
    summary: str = Field(..., description="AI-generated summary")
    tags: list[str] = Field(
        default_factory=list,
        description="Note tags from frontmatter"
    )
    relevance_score: float = Field(
        default=0.5,
        description="Confidence score 0-1"
    )
    match_reason: str = Field(
        default="Content and metadata match",
        description="Why this result was relevant"
    )
    metadata: dict[str, str | bool | int | float | list[dict | list[str]] | None] = Field(
        default_factory=dict,
        description="Note metadata"
    )


class SearchPattern(BaseModel):
    """Reusable search patterns that users can customize."""
    
    name: str = Field(..., description="Human-readable pattern name")
    description: str = Field(
        default="", description="Natural language pattern description"
    )
    query_template: str = Field(..., description="Template for agent prompts")
    filters_template: dict[str, dict] = Field(
        default_factory=dict,
        description="Template for generated search parameters"
    )
    common_queries: list[str] = Field(
        default_factory=list,
        description="Example queries this pattern handles"
    )
    usage_count: int = Field(
        default=0,
        description="How many times this pattern has been used"
    )
    last_used: Optional[datetime] = Field(
        default=None,
        description="Last time this pattern was used"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this pattern was created"
    )


class SearchAnalytics(BaseModel):
    """Analytics data tracking search performance and patterns."""
    
    success_metrics: dict[str, float | int] = Field(
        default_factory=dict,
        description="Performance metrics for search operations"
    )
    usage_patterns: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="Search pattern usage frequency data"
    )
    user_preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="Learned user preferences and behavior"
    )
    vault_structure: dict[str, int] = Field(
        default_factory=dict,
        description="Vault structure analysis for optimization"
    )


class ClassificationResult(BaseModel):
    """Result of automatic note classification."""
    
    classification: str = Field(
        default="unclassified",
        description="Suggested category for the note"
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence level in classification"
    )
    reasoning: str = Field(
        default="",
        description="Why this classification was chosen"
    )
    suggested_actions: list[str] = Field(
        default_factory=[],
        description="Recommended follow-up actions"
    )
