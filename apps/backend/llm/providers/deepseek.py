"""
DeepSeek provider — uses the OpenAI-compatible API.
Supports deepseek-chat (DeepSeek-V3) and deepseek-reasoner (DeepSeek-R1).
Model is configured in config/llm_config.yaml under providers.deepseek.model.
Requires DEEPSEEK_API_KEY in .env.
"""

import os

from apps.backend.llm.base_provider import BaseProvider, LLMConfig
from apps.utils.logging import get_logger

logger = get_logger(__name__)

_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekProvider(BaseProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from openai import OpenAI

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise KeyError("DEEPSEEK_API_KEY not set in .env")

        self._client = OpenAI(api_key=api_key, base_url=_DEEPSEEK_BASE_URL)

    def call(self, system_prompt: str, user_prompt: str) -> str:
        # deepseek-reasoner (R1) does not accept a temperature parameter
        is_reasoner = self.config.model == "deepseek-reasoner"
        logger.debug(
            "DeepSeekProvider calling model=%s temperature=%s max_tokens=%s",
            self.config.model,
            "n/a (reasoner)" if is_reasoner else self.config.temperature,
            self.config.max_tokens,
        )
        try:
            from openai import Omit
            from openai.types.chat import ChatCompletionMessageParam

            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=Omit() if is_reasoner else self.config.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("DeepSeekProvider error: %s", e, exc_info=True)
            raise
