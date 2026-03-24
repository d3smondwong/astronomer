"""
Builds system and user prompts by rendering Jinja2 templates.
"""

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.utils.logging import get_logger

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
        self._system_template = Path(system_template).name
        self._user_template = Path(user_template).name

    def build(self, llm_data: dict) -> tuple[str, str]:
        """Render templates and return (system_prompt, user_prompt)."""
        system_prompt = self._env.get_template(self._system_template).render()
        bazi_json = json.dumps(llm_data, ensure_ascii=False, indent=2)
        user_prompt = self._env.get_template(self._user_template).render(
            bazi_json=bazi_json
        )
        logger.debug(
            "Prompts built — system: %d chars, user: %d chars",
            len(system_prompt),
            len(user_prompt),
        )
        return system_prompt, user_prompt
