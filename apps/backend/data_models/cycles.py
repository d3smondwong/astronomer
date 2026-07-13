"""
Pydantic models for the cycles endpoint (大运 / 流年).
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from apps.backend.data_models.birth_input import BirthInput


class CyclesInput(BirthInput):
    """Birth payload + optional decade selector for lazy 流年 expansion."""

    da_yun_index: Optional[int] = Field(
        default=None,
        ge=0,
        le=9,
        description="大运 index (0-9); when set, that decade's 流年 list is "
                    "populated. Index 0 is the pre-运 period (birth → 起运).",
    )


class CyclesResponse(BaseModel):
    """Response from /v1/chart/cycles — 起运 + fully-analysed 大运 timeline.

    Cycles depend on the exact birth instant (起运 timing), which chart_key
    deliberately excludes — so this response must NEVER be cached under
    chart_key. Cache (if at all) per profileId + da_yun_index at the Next.js
    layer.
    """

    data: Dict[str, Any] = Field(
        ...,
        description="起运 (顺逆/起运阳历/起运计岁) + 大运 list; each 大运 carries "
                    "运柱/作用/神煞/五行动态 and a 流年 list (populated only for "
                    "the requested da_yun_index).",
    )
    chart_key: str = Field(
        ...,
        description="八字-based key returned for log correlation ONLY — not a "
                    "valid cache key for cycle data (excludes the birth instant).",
    )
