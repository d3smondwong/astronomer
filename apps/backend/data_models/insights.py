"""
Pydantic models for the LLM-generated Insights contract.

Scope (for now): personality only. summary / life_aspects are deliberately
omitted and will be added in a later iteration.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List


class Personality(BaseModel):
    """The personality section rendered in the frontend Insights tab."""

    archetype: str = ""
    element: str = ""
    key_traits: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    areas_to_note: List[str] = Field(default_factory=list)

class InsightsRequest(BaseModel):
    """Request for /v1/chart/insights — the natal chart dict from the orchestrator."""

    data: Dict[str, Any] = Field(
        ...,
        description="The Chinese-keyed natal chart output from /v1/chart/natal",
    )


class InsightsResponse(BaseModel):
    """Response from /v1/chart/insights."""

    personality: Personality
