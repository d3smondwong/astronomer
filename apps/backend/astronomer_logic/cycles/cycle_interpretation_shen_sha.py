"""
Cycle Shen Sha Interpretation — 大运/流年 parallel to interpretation_shen_sha.py.

Takes the output of get_cycle_shen_sha() (the single-pillar cycle evaluator) and
enriches each entry with its 大运/流年 解读 drawn from
CYCLE_SHEN_SHA_INTERPRETATIONS.

Unlike the natal interpretation table (keyed by derivation source AND pillar
position for positional prose), the cycle table is keyed by the exact 来源 the
evaluator emits (日干/年干/年支/日支/月支/运柱干支/季节/年柱纳音). Lookup is therefore
a pure exact match — no fallback. That is deliberate: every (名称, 来源) the
evaluator can emit is a direct key (verified by brute-force audit), so a miss
means a genuine key error and should surface as "无" rather than be silently
masked by scanning a sibling source (which would also clobber source-specific
context on multi-source stars like 真词馆 / 童子煞).
"""

from __future__ import annotations

from apps.backend.data.cycle_shen_sha_interpretations import (
    CYCLE_SHEN_SHA_INTERPRETATIONS,
)


def _lookup_cycle_interpretation(name: str, source: str, cycle_type: str) -> str:
    """Exact-match the 大运/流年 interpretation for one cycle shen sha entry."""
    return (
        CYCLE_SHEN_SHA_INTERPRETATIONS
        .get(name, {})
        .get(source, {})
        .get(cycle_type, "无")
    )


def get_cycle_shen_sha_interpretations(cycle_shen_sha: list, cycle_type: str) -> list:
    """
    Enrich cycle (大运/流年) shen sha entries with 解读.

    Args:
        cycle_shen_sha: output of get_cycle_shen_sha() — a flat list of
            entries {"名称": str, "来源": str} (+"细节").
        cycle_type: "大运" or "流年" — selects the interpretation column.

    Returns:
        Same flat list, each entry gaining "解读" (defaults to "无").
    """
    result: list = []
    for entry in cycle_shen_sha:
        entry_out = dict(entry)
        entry_out["解读"] = _lookup_cycle_interpretation(
            entry.get("名称", ""), entry.get("来源", ""), cycle_type
        )
        result.append(entry_out)
    return result
