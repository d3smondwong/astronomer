# Astronomer Application - Architecture & Development Notes

**Last Updated:** February 25, 2026

---

## Project Overview
Building an astronomer application with:
- **Backend:** Python scripts for BaZi calculations + LLM integration
- **Frontend:** React webapp, Android app, iPhone app
- **Current Focus:** Backend architecture

---

## Backend Architecture

### Current Structure (Good)
- `src/main.py` - Entry point
- `src/data.py` - Orchestrator (pulls from calculation modules)
- `src/astronomer_calculations/` - Domain-specific modules
- Returns JSON for LLM consumption

### Recommendations

#### 1. Separate Concerns with a Service Layer

Create a `BaziService` class that orchestrates all calculations:

```python
# filepath: src/services/bazi_service.py
class BaziService:
    """Orchestrates all BaZi calculations"""

    def __init__(self):
        from src.astronomer_calculations import (
            shen_sha,
            interactions_gan_zhi_zuo_yong,
            yuan_tian_gang_bone_weight
        )
        self.shen_sha = shen_sha
        self.interactions = interactions_gan_zhi_zuo_yong
        self.bone_weight = yuan_tian_gang_bone_weight

    def analyze_chart(self, lunar_birthday: Lunar) -> dict:
        """Single entry point for complete analysis"""
        return {
            "shen_sha": self.shen_sha.get_shen_sha(lunar_birthday),
            "interactions": self.interactions.get_interactions(lunar_birthday),
            "bone_weight": self.bone_weight.calculate_yuan_tian_gang_bone_weight(lunar_birthday),
            # Add luck, pillars, etc.
        }
```

#### 2. API Layer (FastAPI)

Expose endpoints for frontend consumption:

```python
# filepath: src/api/routes.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

class BirthInput(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    latitude: float
    longitude: float
    gender: int  # 0=Female, 1=Male

@app.post("/api/bazi/analyze")
async def analyze_bazi(birth: BirthInput):
    """Main endpoint: converts solar → lunar → analysis"""
    try:
        solar = Solar.fromYmdHms(
            birth.year, birth.month, birth.day,
            birth.hour, birth.minute, birth.second
        )
        tst, _ = get_true_solar_time(
            datetime(birth.year, birth.month, birth.day,
                    birth.hour, birth.minute, birth.second),
            birth.latitude, birth.longitude
        )
        lunar = tst.getLunar()

        service = BaziService()
        result = service.analyze_chart(lunar)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### 3. Recommended Project Structure

```
src/
├── main.py                          # FastAPI app initialization
├── config.py                        # Configuration (DB, LLM settings)
├── models/
│   ├── bazi_model.py               # Pydantic models for validation
│   └── response_models.py           # Response schemas
├── services/
│   ├── bazi_service.py             # Orchestrator
│   ├── llm_service.py              # LLM integration
│   └── cache_service.py            # Caching layer
├── api/
│   ├── routes.py                   # FastAPI routes
│   └── middleware.py               # Auth, logging, CORS
├── astronomer_calculations/         # Your existing modules
│   ├── shen_sha.py
│   ├── interactions_gan_zhi_zuo_yong.py
│   ├── yuan_tian_gang_bone_weight.py
│   └── ...
├── utils/
│   ├── solar_lunar_time.py
│   └── validators.py
└── tests/
    ├── test_shen_sha.py
    └── test_api.py
```

#### 4. Caching Strategy

BaZi calculations are deterministic—cache results to improve performance:

```python
# filepath: src/services/cache_service.py
from functools import lru_cache
import hashlib

class CacheService:
    @staticmethod
    def get_cache_key(year: int, month: int, day: int, hour: int, min: int, sec: int, lat: float, lon: float) -> str:
        """Generate consistent cache key"""
        key = f"{year}-{month}-{day}-{hour}-{min}-{sec}-{lat}-{lon}"
        return hashlib.md5(key.encode()).hexdigest()

    @lru_cache(maxsize=10000)
    def get_bazi_analysis(self, cache_key: str, lunar_birthday):
        """Cache analysis results"""
        service = BaziService()
        return service.analyze_chart(lunar_birthday)
```

#### 5. LLM Integration Layer

```python
# filepath: src/services/llm_service.py
class LLMService:
    def __init__(self, model: str = "gpt-4"):
        self.model = model

    def generate_interpretation(self, bazi_data: dict) -> str:
        """Feed structured data to LLM for narrative interpretation"""
        prompt = self._format_prompt(bazi_data)
        # Call your LLM API
        return self._call_llm(prompt)

    @staticmethod
    def _format_prompt(bazi_data: dict) -> str:
        """Structure BaZi data for LLM consumption"""
        return f"""
        Analyze this BaZi chart:
        {json.dumps(bazi_data, ensure_ascii=False, indent=2)}

        Provide insights on: character, destiny, relationships, career potential.
        """
```

---

## Key Considerations

| Aspect | Recommendation |
|--------|-----------------|
| **Database** | Store user profiles (birth info, analysis history) in PostgreSQL |
| **Async** | Use FastAPI's async/await for I/O-heavy ops (LLM calls) |
| **Rate Limiting** | Implement Redis-based rate limiting for API endpoints |
| **Versioning** | API routes: `/api/v1/bazi/analyze` (prep for breaking changes) |
| **Testing** | Unit tests for calculation modules, integration tests for API |
| **Documentation** | OpenAPI/Swagger auto-generated from FastAPI |
| **Deployment** | Docker container + CI/CD pipeline (GitHub Actions) |

---

## Frontend Considerations

### Web (React)
- Consume `/api/v1/bazi/analyze` endpoint
- Can request full data or paginated sections
- Display LLM interpretation alongside structured data

### Mobile (Android/iPhone)
- Same API endpoint reduces backend complexity
- Lighter UI for mobile screens
- Consider offline-first architecture with local caching

### Single Entry Point
- **Endpoint:** `/api/v1/bazi/analyze`
- **Input:** Birth date, time, location, gender
- **Output:** Complete BaZi analysis JSON + LLM interpretation

---

## Development Checklist

- [ ] Refactor `data.py` into `BaziService` class
- [ ] Set up FastAPI project structure
- [ ] Create Pydantic models for request/response validation
- [ ] Implement `/api/v1/bazi/analyze` endpoint
- [ ] Add caching layer for deterministic calculations
- [ ] Integrate LLM service
- [ ] Write unit tests for calculation modules
- [ ] Write integration tests for API
- [ ] Set up Docker configuration
- [ ] Configure CORS for frontend domains
- [ ] Implement API authentication (if needed)
- [ ] Set up database for user profiles

---

## Notes
- Current orchestrator approach in `data.py` is solid—just wrap it in an API layer
- All calculation modules should be stateless and deterministic
- Cache keys should include location data (affects solar/lunar conversions)