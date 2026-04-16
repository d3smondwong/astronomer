"""
Chart calculation endpoints.

POST /v1/chart/natal — basic natal chart (4 pillars, 10 gods, life stages, na yin, void, 3 palaces)
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from apps.backend.data_models.birth_input import BirthInput, NatalChartResponse
from apps.backend.orchestrator.astronomer_data_orchestrator import calculate_natal_chart

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
