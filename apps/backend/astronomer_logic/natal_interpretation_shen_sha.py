"""
Shen Sha Interpretation Module

Takes the output of get_shen_sha() and returns a combined nested structure
that enriches each shen sha entry with an interpretation (解读) based on:
  1. 来源 (Source of Derivation) — e.g. 月支, 日干
  2. 柱位 (Pillar Occupied)     — 年柱, 月柱, 日柱, 时柱

Output format:
  {
    "神煞": {
      "年柱": [{"名称": str, "来源": str, "解读": str | None}, ...],
      "月柱": [...],
      "日柱": [...],
      "时柱": [...],
    }
  }

Shen sha without a matching interpretation entry carry "解读": "无".
This output is intended to replace the raw shen_sha dict in the orchestrator.
"""

from __future__ import annotations

from apps.backend.data.natal_shen_sha_interpretations import (
    NATAL_SHEN_SHA_INTERPRETATIONS,
)

_PILLAR_KEYS = ["年柱", "月柱", "日柱", "时柱"]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_shen_sha_interpretations(shen_sha_result: dict) -> dict:
    """
    Enrich raw shen sha data with interpretations and return a unified structure.

    Args:
        shen_sha_result: Output of get_shen_sha() — {"神煞": {"柱位神煞": {...}}}

    Returns:
        {"神煞": {"年柱": [...], "月柱": [...], "日柱": [...], "时柱": [...]}}
        Each entry: {"名称": str, "来源": str, "解读": str, "interpretation": str}
    """
    raw_pillars: dict = shen_sha_result.get("神煞", {})

    result: dict[str, list] = {}
    for pillar in _PILLAR_KEYS:
        entries = raw_pillars.get(pillar, {}).get("神煞", [])
        enriched = []
        for entry in entries:
            name: str = entry.get("名称", "")
            source: str = entry.get("来源", "")
            detail: str = entry.get("细节", "")
            lookup_key: str = detail if detail else pillar
            interpretation_ch: str = (
                NATAL_SHEN_SHA_INTERPRETATIONS
                .get(name, {})
                .get(source, {})
                .get(lookup_key, "无")
            )
            entry_out: dict = {
                "名称": name,
                "来源": source,
                "解读": interpretation_ch,
            }
            if detail:
                entry_out["细节"] = detail
            enriched.append(entry_out)
        if enriched:
            result[pillar] = enriched

    return {"神煞": result}

# ============================================================================
# EXECUTION
# python -m apps.backend.astronomer_logic.natal_interpretation_shen_sha
# ============================================================================

if __name__ == "__main__":
    import json
    from datetime import datetime

    from lunar_python import Solar
    from apps.backend.astronomer_logic.na_yin import get_na_yin
    from apps.backend.astronomer_logic.natal_shen_sha import get_shen_sha

    subjects = {
        "Desmond": (datetime(1985, 11, 25, 17, 7, 0),  1),
        # "Corinne": (datetime(1987,  6,  3, 12, 6, 0),  0),
        # "Lara":    (datetime(2025,  7, 31,  9, 10, 0), 0),
    }

    for subject_name, (birthday, gender) in subjects.items():
        print("=" * 60)
        print(f"Subject: {subject_name}  ({birthday.strftime('%Y-%m-%d %H:%M')})")

        solar = Solar.fromYmdHms(
            birthday.year, birthday.month, birthday.day,
            birthday.hour, birthday.minute, birthday.second,
        )
        lunar = solar.getLunar()
        bazi  = lunar.getEightChar()

        na_yin   = get_na_yin(bazi)
        shen_sha = get_shen_sha(bazi, na_yin, gender)
        result   = get_shen_sha_interpretations(shen_sha)

        print(json.dumps(result, ensure_ascii=False, indent=2))