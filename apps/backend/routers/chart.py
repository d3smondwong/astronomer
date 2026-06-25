"""
Chart calculation endpoints.

POST /v1/chart/natal     — basic natal chart (4 pillars, 10 gods, life stages, na yin, void, 3 palaces)
POST /v1/chart/insights  — LLM-generated personality insights from a natal chart
"""

from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Header
from apps.backend.data_models.birth_input import BirthInput, NatalChartResponse
from apps.backend.data_models.insights import (
    InsightsRequest,
    InsightsResponse,
)
from apps.backend.orchestrator.astronomer_data_orchestrator import calculate_natal_chart
from apps.backend.llm.llm_service import llm_analyse_bazi, llm_analyse_section, LLMError
from apps.backend.llm.section_registry import SECTION_REGISTRY
from apps.utils.logging import get_logger, request_id_var

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/chart", tags=["chart"])


@router.post("/natal", response_model=NatalChartResponse)
async def calculate_natal(input_data: BirthInput) -> NatalChartResponse:
    """
    Calculate natal chart (4 pillars with all Phase 1 modules).

    Returns:
        NatalChartResponse with all Chinese-keyed data under the 'data' key.
    """
    try:
        # Reconstruct datetime from flat fields
        birth_datetime = datetime(
            year=input_data.year,
            month=input_data.month,
            day=input_data.day,
            hour=input_data.hour,
            minute=input_data.minute,
            second=0,
        )

        # Call the orchestrator (returns Chinese-keyed dict)
        natal_chart = calculate_natal_chart(
            birth_datetime=birth_datetime,
            latitude=input_data.latitude,
            longitude=input_data.longitude,
            gender=input_data.gender,
            use_solar_time_correction=input_data.use_solar_time_correction,
        )

        # Return the raw orchestrator output
        return NatalChartResponse(data=natal_chart)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/insights", response_model=InsightsResponse)
async def generate_insights(
    request: InsightsRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
) -> InsightsResponse:
    """
    Generate the multi-section insight report from an already-computed natal chart.

    Takes the chart dict (output of /v1/chart/natal) and runs it through the
    configured LLM provider — one call per life-domain section. Kept separate from
    chart calculation so the slow, non-deterministic LLM step never blocks or
    breaks chart rendering.

    Binds the incoming X-Request-Id (or a generated one) so every log line for this
    request — across llm_service and the provider — carries the same id for tracing.
    """
    request_id_var.set(x_request_id or uuid4().hex[:12])

    # Single-section path (progressive/parallel loading from the frontend).
    if request.section:
        valid_keys = {s.key for s in SECTION_REGISTRY}
        if request.section not in valid_keys:
            logger.warning("insights_bad_section | section=%s", request.section)
            raise HTTPException(status_code=422, detail=f"Unknown section: {request.section}")
        try:
            text = llm_analyse_section(request.data, request.section)
        except LLMError as e:
            logger.error("insights_section_failed | section=%s | %s", request.section, e)
            raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")
        except Exception as e:
            logger.exception("insights_section_error | section=%s", request.section)
            raise HTTPException(status_code=500, detail=f"Insights error: {str(e)}")
        logger.info(
            "insights_section_ok | section=%s | chars=%d", request.section, len(text)
        )
        return InsightsResponse(sections={request.section: text})

    # Full-report path.
    try:
        report = llm_analyse_bazi(request.data)
    except LLMError as e:
        logger.error("insights_report_failed | %s", e)
        raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")
    except Exception as e:
        logger.exception("insights_report_error")
        raise HTTPException(status_code=500, detail=f"Insights error: {str(e)}")

    return InsightsResponse(sections=report.sections)
