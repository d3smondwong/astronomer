"""
Pydantic models for birth input and chart responses.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict


class BirthInput(BaseModel):
    """Input for birth data — wall-clock time, location, gender."""
    year: int = Field(..., description="Birth year (gregorian)")
    month: int = Field(..., ge=1, le=12, description="Birth month (1-12)")
    day: int = Field(..., ge=1, le=31, description="Birth day (1-31)")
    hour: int = Field(..., ge=0, le=23, description="Birth hour (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Birth minute (0-59)")
    gender: int = Field(..., description="1 = male, 0 = female")
    latitude: float = Field(..., description="Birth location latitude (decimal degrees)")
    longitude: float = Field(..., description="Birth location longitude (decimal degrees)")
    use_solar_time_correction: bool = Field(
        default=True,
        description="If true, apply True Solar Time correction (longitude + Equation of Time)",
    )


class NatalChartResponse(BaseModel):
    """Response from /v1/chart/natal — basic 4 pillars."""
    data: Dict[str, Any] = Field(
        ...,
        description="农历生日, 性别, 生肖, 四柱实体, 胎命身, etc.",
    )
