"""
Anthropic Claude LLM provider.
"""

import os

from apps.backend.llm.base_provider import BaseProvider, LLMConfig
from apps.utils.logging import get_logger

logger = get_logger(__name__)


class ClaudeProvider(BaseProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise KeyError("ANTHROPIC_API_KEY not set in .env")

        self._client = anthropic.Anthropic(api_key=api_key)

    def call(self, system_prompt: str, user_prompt: str) -> str:
        logger.debug(
            "ClaudeProvider calling model=%s temperature=%s max_tokens=%s",
            self.config.model,
            self.config.temperature,
            self.config.max_tokens,
        )
        try:
            import anthropic

            message = self._client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=self.config.temperature,
            )
            return message.content[0].text
        except anthropic.APIError as e:
            logger.error("ClaudeProvider API error: %s", e, exc_info=True)
            raise
        except Exception as e:
            logger.error("ClaudeProvider unexpected error: %s", e, exc_info=True)
            raise
