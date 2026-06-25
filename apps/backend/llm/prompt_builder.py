"""
Builds system and user prompts by rendering Jinja2 templates.
"""

import json
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from lunar_python import Solar

from apps.backend.llm.section_registry import Section
from apps.utils.logging import get_logger

logger = get_logger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"


class PromptBuilder:
    def __init__(self, system_template: str, user_template: str):
        """
        Args:
            system_template: Relative path to system prompt .jinja file (from prompts dir).
            user_template:   Relative path to user prompt .jinja file (from prompts dir).
        """
        self._env = Environment(
            loader=FileSystemLoader(str(_PROMPTS_DIR)),
            keep_trailing_newline=True,
        )
        self._env.policies["json.dumps_kwargs"] = {"ensure_ascii": False}
        self._system_template = Path(system_template).name
        self._user_template = Path(user_template).name

    def build(self, section: Section, chart: dict) -> tuple[str, str]:
        """Render the shared system prompt and the per-section user prompt.

        Args:
            section: The section being generated (drives title/guidance/emphasis/key).
            chart:   The full natal chart dict — passed whole, never sliced.

        Returns:
            (system_prompt, user_prompt)
        """
        system_prompt = self._env.get_template(self._system_template).render()
        bazi_json = json.dumps(chart, ensure_ascii=False, indent=2)
        user_prompt = self._env.get_template(self._user_template).render(
            section=section,
            bazi_json=bazi_json,
            current_year=Solar.fromDate(datetime.now()).getLunar().getYear(),
        )
        logger.debug(
            "Prompts built [%s] — system: %d chars, user: %d chars",
            section.key,
            len(system_prompt),
            len(user_prompt),
        )
        return system_prompt, user_prompt
