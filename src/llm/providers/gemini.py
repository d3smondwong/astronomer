"""
Google Gemini LLM provider.
"""

import os

from src.llm.base_provider import BaseProvider, LLMConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise KeyError("GEMINI_API_KEY not set in .env")

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_client = genai.GenerativeModel(
            model_name=config.model,
            system_instruction=None,  # system prompt passed per-call via contents
        )

    def call(self, system_prompt: str, user_prompt: str) -> str:
        logger.debug(
            "GeminiProvider calling model=%s temperature=%s max_tokens=%s",
            self.config.model,
            self.config.temperature,
            self.config.max_tokens,
        )
        try:
            # Gemini supports a system instruction at model level; rebuild with it
            model = self._genai.GenerativeModel(
                model_name=self.config.model,
                system_instruction=system_prompt,
            )
            response = model.generate_content(
                user_prompt,
                generation_config=self._genai.GenerationConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens,
                ),
            )
            return response.text
        except Exception as e:
            logger.error("GeminiProvider error: %s", e, exc_info=True)
            raise
