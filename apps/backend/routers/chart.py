"""
Chart calculation endpoints.

POST /v1/chart/natal     — basic natal chart (4 pillars, 10 gods, life stages, na yin, void, 3 palaces)
POST /v1/chart/insights  — LLM-generated personality insights from a natal chart
"""

import json
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse
from apps.backend.data_models.birth_input import BirthInput, NatalChartResponse
from apps.backend.data_models.insights import (
    InsightsRequest,
    InsightsResponse,
)
from apps.backend.orchestrator.astronomer_data_orchestrator import calculate_natal_chart
from apps.backend.llm.llm_service import (
    llm_analyse_bazi,
    llm_analyse_section,
    llm_analyse_section_stream,
    LLMError,
)
from apps.backend.llm.section_registry import SECTION_REGISTRY
from apps.utils.logging import (
    get_logger,
    request_id_var,
    profile_id_var,
    uid_var,
    chart_key_var,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/chart", tags=["chart"])


async def bind_log_context(
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
    x_chart_key: str | None = Header(default=None, alias="X-Chart-Key"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_profile_id: str | None = Header(default=None, alias="X-Profile-Id"),
) -> None:
    """Bind per-request log context from the incoming X-* headers (set by the Next.js
    route handlers) so every log line for this request — across modules and the LLM
    provider — carries the same correlation ids for tracing.

    Sets all four contextvars on every call (defaulting to "-", or a minted id for the
    request id) so a value never bleeds from a prior request sharing the same context.
    """
    request_id_var.set(x_request_id or uuid4().hex[:12])
    chart_key_var.set(x_chart_key or "-")
    uid_var.set(x_user_id or "-")
    profile_id_var.set(x_profile_id or "-")


@router.post("/natal", response_model=NatalChartResponse)
async def calculate_natal(
    input_data: BirthInput,
    _ctx: None = Depends(bind_log_context),
) -> NatalChartResponse:
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

        # Call the orchestrator (returns Chinese-keyed dict + the 八字-based cache key)
        natal_chart, chart_key = calculate_natal_chart(
            birth_datetime=birth_datetime,
            latitude=input_data.latitude,
            longitude=input_data.longitude,
            gender=input_data.gender,
            use_solar_time_correction=input_data.use_solar_time_correction,
        )

        # Bind the computed key so this request's log lines carry [chart:…] even though
        # the natal call is the one that *produces* the key (no X-Chart-Key header inbound).
        chart_key_var.set(chart_key)

        # Return the raw orchestrator output plus the cache key
        return NatalChartResponse(data=natal_chart, chart_key=chart_key)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/insights", response_model=InsightsResponse)
async def generate_insights(
    request: InsightsRequest,
    _ctx: None = Depends(bind_log_context),
) -> InsightsResponse:
    """
    Generate the multi-section insight report from an already-computed natal chart.

    Takes the chart dict (output of /v1/chart/natal) and runs it through the
    configured LLM provider — one call per life-domain section. Kept separate from
    chart calculation so the slow, non-deterministic LLM step never blocks or
    breaks chart rendering.

    The X-* headers (bound by ``bind_log_context``) make every log line for this
    request — across llm_service and the provider — carry the same correlation ids.
    """
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


@router.post("/insights/stream")
async def stream_insights(
    request: InsightsRequest,
    _ctx: None = Depends(bind_log_context),
) -> StreamingResponse:
    """Stream one insight section as Server-Sent Events of group-deltas.

    Each event is ``data: {"section": "<key>", "delta": {<group>: [items]}}`` emitted
    as soon as that group finishes generating, followed by a terminal ``data: [DONE]``.
    Using the async streaming path keeps the event loop free, so the frontend's
    parallel per-section requests actually run concurrently.
    """
    section = request.section
    if not section:
        raise HTTPException(status_code=422, detail="section is required for streaming")
    valid_keys = {s.key for s in SECTION_REGISTRY}
    if section not in valid_keys:
        logger.warning("insights_bad_section | section=%s", section)
        raise HTTPException(status_code=422, detail=f"Unknown section: {section}")

    # Capture the request context bound by bind_log_context. The SSE body below is
    # iterated by Starlette *after* this function returns, in a separate execution
    # context where these contextvar values are not visible — so re-bind them inside
    # the generator, else every streamed log line falls back to the "-" defaults.
    log_ctx = (
        request_id_var.get(),
        profile_id_var.get(),
        uid_var.get(),
        chart_key_var.get(),
    )

    async def event_source():
        request_id_var.set(log_ctx[0])
        profile_id_var.set(log_ctx[1])
        uid_var.set(log_ctx[2])
        chart_key_var.set(log_ctx[3])
        try:
            async for delta in llm_analyse_section_stream(request.data, section):
                payload = json.dumps(
                    {"section": section, "delta": delta}, ensure_ascii=False
                )
                yield f"data: {payload}\n\n"
        except Exception:
            logger.exception("insights_stream_error | section=%s", section)
            # Surface a structured error event; the client treats a stream that ends
            # without [DONE] (or with an error event) as a failure.
            yield 'data: {"error": "stream_failed"}\n\n'
            return
        logger.info("insights_stream_ok | section=%s", section)
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable proxy buffering so deltas flush live
        },
    )
