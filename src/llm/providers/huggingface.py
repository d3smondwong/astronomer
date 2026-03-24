"""
Hugging Face Inference API provider.
Supports any chat-completion compatible model via InferenceClient.
Model is configured in config/llm_config.yaml under providers.huggingface.model.
"""

import os

from src.llm.base_provider import BaseProvider, LLMConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HuggingFaceProvider(BaseProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from huggingface_hub import InferenceClient

        api_key = os.environ.get("HUGGINGFACE_API_KEY")
        if not api_key:
            raise KeyError("HUGGINGFACE_API_KEY not set in .env")

        self._client = InferenceClient(
            model=config.model,
            token=api_key,
        )

    def call(self, system_prompt: str, user_prompt: str) -> str:
        logger.debug(
            "HuggingFaceProvider calling model=%s temperature=%s max_tokens=%s",
            self.config.model,
            self.config.temperature,
            self.config.max_tokens,
        )
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = self._client.chat_completion(
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("HuggingFaceProvider error: %s", e, exc_info=True)
            raise
