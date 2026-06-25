"""
Parses a raw per-section LLM response into the narrative string for that section.
"""

import json
import re

from json_repair import repair_json

from apps.utils.logging import get_logger

logger = get_logger(__name__)


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
    def parse_section(self, section_key: str, raw_text: str) -> str:
        """Extract the narrative prose for one section from a JSON LLM response.

        Expects ``{"<section_key>": "<narrative>"}``. Falls back gracefully:
        if the wrapper key is missing, returns the first string value or the
        cleaned raw text; on total parse failure returns "" so one bad section
        never aborts the whole report.
        """
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
                    logger.debug(
                        "ResponseParser[%s]: json-repair recovered malformed JSON",
                        section_key,
                    )
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(
                        "ResponseParser[%s]: JSON decode failed (%s) — using raw text",
                        section_key,
                        e,
                    )
                    return text

        if isinstance(data, dict):
            # Preferred: the exact section key.
            if section_key in data:
                narrative = _as_str(data[section_key]).strip()
            else:
                # Model omitted/renamed the wrapper — take the first string value.
                narrative = next(
                    (_as_str(v).strip() for v in data.values() if isinstance(v, str)),
                    "",
                )
            if not narrative:
                logger.warning(
                    "ResponseParser[%s]: parsed JSON had no narrative string", section_key
                )
        elif isinstance(data, str):
            narrative = data.strip()
        else:
            narrative = ""

        logger.debug(
            "Parsed section [%s] — %d chars", section_key, len(narrative)
        )
        return narrative
