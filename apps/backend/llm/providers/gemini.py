"""
Google Gemini LLM provider.
"""

import os

from apps.backend.llm.base_provider import BaseProvider, LLMConfig
from apps.utils.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from google import genai
        from google.genai import types

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise KeyError("GEMINI_API_KEY not set in .env")

        self._client = genai.Client(api_key=api_key)
        self._types = types

    def call(self, system_prompt: str, user_prompt: str) -> str:
        from google.genai import errors

        logger.debug(
            "GeminiProvider calling model=%s temperature=%s max_tokens=%s",
            self.config.model,
            self.config.temperature,
            self.config.max_tokens,
        )
        try:
            response = self._client.models.generate_content(
                model=self.config.model,
                contents=user_prompt,
                config=self._types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens,
                ),
            )
        except errors.APIError as e:
            # Base class for client (4xx) and server (5xx) errors. Code bugs
            # deliberately propagate unmasked.
            logger.error(
                "Gemini API error (model=%s, code=%s): %s",
                self.config.model,
                getattr(e, "code", None),
                e,
                exc_info=True,
            )
            raise

        # Token usage — `cached_content_token_count` reflects implicit-cache hits on the
        # shared chart+persona prefix (see llm_config gemini model). Fields may be None.
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            logger.info(
                "Gemini usage: prompt=%s cached=%s output=%s total=%s",
                getattr(usage, "prompt_token_count", None),
                getattr(usage, "cached_content_token_count", None),
                getattr(usage, "candidates_token_count", None),
                getattr(usage, "total_token_count", None),
            )
        return response.text
