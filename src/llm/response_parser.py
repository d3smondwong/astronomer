"""
Parses the raw LLM response into structured Life Overview, Romance, and Career sections.
"""

import json
import re

from json_repair import repair_json

from src.llm.base_provider import LifeOverview, LLMResponse
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _normalize_newlines(text) -> str:
    """Ensure single newlines become markdown hard-breaks so st.markdown renders them."""
    if text is None:
        return ""
    if not isinstance(text, str):
        # LLM returned a list — convert to bullet points
        if isinstance(text, list):
            lines = []
            closing = ""
            for item in text:
                if not isinstance(item, str):
                    continue
                item = item.strip()
                if item.startswith("*If") or item.startswith("If"):
                    closing = item
                else:
                    if not item.startswith("- "):
                        item = f"- {item}"
                    lines.append(item)
            if closing:
                lines.append(f"\n{closing}")
            text = "\n".join(lines)
        else:
            # Other non-string (e.g. nested dict) — serialize so content isn't lost
            try:
                text = json.dumps(text, ensure_ascii=False)
            except Exception:
                return ""
    if not text:
        return text
    # Replace literal \n escape sequences the LLM sometimes emits inside JSON strings
    text = text.replace("\\n", "\n")
    # Collapse 3+ newlines to 2 (paragraph break), then expand single newlines to hard breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n(?!\n)", "  \n", text)
    return text


def _flatten_core_areas(value) -> str:
    """Convert core_areas dict (wealth/relationships/career) to a headed markdown string."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        section_headers = {
            "wealth": "#### 💰 Wealth",
            "relationships": "#### 💕 Relationships",
            "career": "#### 💼 Career",
            "health": "#### 🌿 Health",
        }
        parts = []
        for key, header in section_headers.items():
            text = value.get(key, "")
            if text:
                parts.append(f"{header}\n{text}")
        return "\n\n".join(parts)
    return ""


# Strip markdown code fences the model sometimes wraps around JSON
_CODE_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _repair_json_strings(text: str) -> str:
    """Escape literal control characters inside JSON string values.

    LLMs sometimes emit literal newlines/tabs inside JSON string values, which
    makes json.loads() fail. This walks the text character-by-character and
    escapes those characters only when inside a string value.
    """
    result = []
    in_string = False
    escaped = False
    for char in text:
        if escaped:
            result.append(char)
            escaped = False
        elif char == "\\":
            result.append(char)
            escaped = True
        elif char == '"':
            in_string = not in_string
            result.append(char)
        elif in_string and char == "\n":
            result.append("\\n")
        elif in_string and char == "\r":
            result.append("\\r")
        elif in_string and char == "\t":
            result.append("\\t")
        else:
            result.append(char)
    return "".join(result)


class ResponseParser:
    def parse(self, raw_text: str) -> LLMResponse:
        """Extract life_overview (nested), romance, and career from a JSON LLM response."""
        text = raw_text.strip()

        # Unwrap ```json ... ``` if present
        fence_match = _CODE_FENCE.search(text)
        if fence_match:
            text = fence_match.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Try manual control-character escaping first (fast path)
            try:
                data = json.loads(_repair_json_strings(text))
            except json.JSONDecodeError:
                # Fall back to json-repair which handles unescaped quotes, missing commas, etc.
                try:
                    data = json.loads(repair_json(text))
                    logger.debug("ResponseParser: json-repair recovered malformed JSON")
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning("ResponseParser: JSON decode failed (%s) — returning raw text", e)
                    return LLMResponse(life_overview=LifeOverview(), romance="", career="", raw_text=raw_text)

        raw_overview = data.get("retrospective")
        # Support both the new nested-object format and the legacy flat-string format
        if isinstance(raw_overview, str):
            life_overview = LifeOverview(poem=_normalize_newlines(raw_overview))
        else:
            life_overview = LifeOverview(
                poem=_normalize_newlines(raw_overview.get("poem", "")),
                self_verification=_normalize_newlines(raw_overview.get("self_verification", "")),
                core_identity=_normalize_newlines(raw_overview.get("core_identity", "")),
                core_areas=_normalize_newlines(_flatten_core_areas(raw_overview.get("core_areas", ""))),
                defining_events=_normalize_newlines(raw_overview.get("defining_events", "")),
                life_so_far=_normalize_newlines(raw_overview.get("life_so_far", "")),
                # the_future=_normalize_newlines(raw_overview.get("the_future", "")),
                # destiny_balance_sheet=_normalize_newlines(raw_overview.get("destiny_balance_sheet", "")),
                # living_in_alignment=_normalize_newlines(raw_overview.get("living_in_alignment", "")),
            )

        romance = _normalize_newlines(data.get("romance", ""))
        career = _normalize_newlines(data.get("career", ""))

        total_chars = sum(len(v) for v in vars(life_overview).values())
        logger.debug(
            "Parsed sections — Life Overview: %d chars total (%d sub-sections filled), Romance: %d chars, Career: %d chars",
            total_chars,
            sum(1 for v in vars(life_overview).values() if v),
            len(romance),
            len(career),
        )

        return LLMResponse(
            life_overview=life_overview,
            romance=romance,
            career=career,
            raw_text=raw_text,
        )
