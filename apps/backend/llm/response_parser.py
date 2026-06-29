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
    def parse_section(
        self, section_key: str, raw_text: str, structured: bool = False, quiet: bool = False
    ) -> str | dict:
        """Extract one section's payload from a JSON LLM response.

        Prose sections (``structured=False``) expect ``{"<section_key>": "<narrative>"}``
        and return a string. Structured sections (``structured=True``) expect
        ``{"<section_key>": {<group>: [{"point", "explanation"}, ...]}}`` and return
        the inner object dict.

        Both degrade gracefully: on total parse failure a prose section returns the
        cleaned raw text and a structured section returns ``{}``, so one bad section
        never aborts the whole report.

        ``quiet`` suppresses warning/debug logs — used when parsing the still-growing
        buffer on every streaming delta, where transient parse failures are expected
        and would otherwise flood the logs.
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
                    if not quiet:
                        logger.debug(
                            "ResponseParser[%s]: json-repair recovered malformed JSON",
                            section_key,
                        )
                except (json.JSONDecodeError, Exception) as e:
                    if not quiet:
                        logger.warning(
                            "ResponseParser[%s]: JSON decode failed (%s) — using raw text",
                            section_key,
                            e,
                        )
                    return {} if structured else text

        if structured:
            return self._extract_structured(section_key, data, quiet=quiet)
        return self._extract_prose(section_key, data, quiet=quiet)

    def _extract_prose(self, section_key: str, data, quiet: bool = False) -> str:
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
            if not narrative and not quiet:
                logger.warning(
                    "ResponseParser[%s]: parsed JSON had no narrative string", section_key
                )
        elif isinstance(data, str):
            narrative = data.strip()
        else:
            narrative = ""

        if not quiet:
            logger.debug("Parsed section [%s] — %d chars", section_key, len(narrative))
        return narrative

    def _extract_structured(self, section_key: str, data, quiet: bool = False) -> dict:
        """Pull the inner groups object out of a structured section response."""
        if isinstance(data, dict):
            # Preferred: the wrapper key holds the groups object. If the model
            # dropped the wrapper and returned the groups directly, use data itself.
            inner = data.get(section_key, data)
            if isinstance(inner, dict):
                groups = sum(len(v) for v in inner.values() if isinstance(v, list))
                if not quiet:
                    logger.debug(
                        "Parsed structured section [%s] — %d groups, %d items",
                        section_key,
                        len(inner),
                        groups,
                    )
                return inner

        if not quiet:
            logger.warning(
                "ResponseParser[%s]: expected a structured object, got %s",
                section_key,
                type(data).__name__,
            )
        return {}
