"""
Pydantic models for the LLM-generated Insights contract.

The report is multi-section narrative prose: one string per life domain
(personality, family, romance, career, wealth, health).
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class InsightsRequest(BaseModel):
    """Request for /v1/chart/insights — the natal chart dict from the orchestrator."""

    data: Dict[str, Any] = Field(
        ...,
        description="The Chinese-keyed natal chart output from /v1/chart/natal",
    )
    section: Optional[str] = Field(
        default=None,
        description=(
            "If set, generate only this one section (e.g. 'personality') for "
            "progressive/parallel loading. If omitted, generate the full report."
        ),
    )


class InsightsResponse(BaseModel):
    """Response from /v1/chart/insights.

    sections: section key (e.g. "personality") -> the section payload: narrative
        prose (str) for most domains, or a structured groups object for sections
        that define categories (e.g. "career": {group: [{point, explanation}]}).
    """

    sections: Dict[str, Any] = Field(default_factory=dict)
