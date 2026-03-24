"""
Parses the raw LLM response into structured Life Overview, Romance, and Career sections.
"""

import re

from src.llm.base_provider import LLMResponse
from src.utils.logging import get_logger

logger = get_logger(__name__)

_SECTION_PATTERN = re.compile(
    r"##\s*Life Overview\s*|##\s*Romance\s*|##\s*Career\s*",
    re.IGNORECASE,
)


class ResponseParser:
    def parse(self, raw_text: str) -> LLMResponse:
        """Split raw LLM text into the three BaZi analysis sections."""
        parts = _SECTION_PATTERN.split(raw_text)
        # parts[0] is any preamble before the first header (usually empty)
        # parts[1], [2], [3] are the section bodies
        sections = [p.strip() for p in parts[1:4]]

        # Pad to 3 if model returned fewer sections
        while len(sections) < 3:
            sections.append("")

        life_overview, romance, career = sections[0], sections[1], sections[2]

        logger.debug(
            "Parsed sections — Life Overview: %d chars, Romance: %d chars, Career: %d chars",
            len(life_overview),
            len(romance),
            len(career),
        )

        return LLMResponse(
            life_overview=life_overview,
            romance=romance,
            career=career,
            raw_text=raw_text,
        )
