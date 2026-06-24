"""
Parses the raw LLM response into the structured Insights contract (personality).
"""

import json
import re

from json_repair import repair_json

from apps.backend.llm.base_provider import InsightsResponse, Personality
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _as_str_list(value) -> list[str]:
    """Coerce an LLM value into a clean list of strings.

    Accepts a list (filtered to non-empty strings) or a single string
    (comma-separated or one item). Anything else becomes an empty list.
    """
    if value is None:
        return []
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        # Split comma-separated strings the model sometimes returns instead of a list
        parts = [p.strip() for p in value.split(",")]
        return [p for p in parts if p]
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, str):
                item = item.strip()
                if item:
                    out.append(item)
            elif item is not None:
                out.append(str(item))
        return out
    return []


def _as_str(value) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


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
    def parse(self, raw_text: str) -> InsightsResponse:
        """Extract the personality section from a JSON LLM response."""
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
                    logger.warning(
                        "ResponseParser: JSON decode failed (%s) — returning empty personality", e
                    )
                    return InsightsResponse(personality=Personality(), raw_text=raw_text)

        # Support both {"personality": {...}} and a flat top-level object
        block = data.get("personality") if isinstance(data, dict) else None
        if not isinstance(block, dict):
            block = data if isinstance(data, dict) else {}

        personality = Personality(
            archetype=_as_str(block.get("archetype", "")),
            element=_as_str(block.get("element", "")),
            key_traits=_as_str_list(block.get("key_traits")),
            strengths=_as_str_list(block.get("strengths")),
            areas_to_note=_as_str_list(block.get("areas_to_note")),
            lucky_colors=_as_str_list(block.get("lucky_colors")),
            lucky_numbers=_as_str_list(block.get("lucky_numbers")),
        )

        logger.debug(
            "Parsed personality — archetype=%r element=%r traits=%d strengths=%d areas=%d colors=%d numbers=%d",
            personality.archetype,
            personality.element,
            len(personality.key_traits),
            len(personality.strengths),
            len(personality.areas_to_note),
            len(personality.lucky_colors),
            len(personality.lucky_numbers),
        )

        return InsightsResponse(personality=personality, raw_text=raw_text)
