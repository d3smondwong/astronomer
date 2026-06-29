"""
DeepSeek provider — calls deepseek-v4-flash (or deepseek-v4-pro) through the
OpenAI-compatible Chat Completions API.

Thinking vs. non-thinking is now a *mode* of a single model, not a separate
model name (the old deepseek-chat / deepseek-reasoner aliases are deprecated):
toggle it with the DeepSeek-specific ``thinking`` object, passed via the OpenAI
SDK's ``extra_body``. Both switches live in config/llm_config.yaml under
providers.deepseek (``thinking`` / ``reasoning_effort``). ``temperature`` only
takes effect in non-thinking mode — thinking mode silently ignores it.

Context caching is automatic on DeepSeek — no setup. Requests sharing a prefix
are billed at the cheaper cache-hit rate. Our six section calls per chart share
the same system prompt and the chart JSON placed first in the user prompt, so
that whole block is a cache prefix after the first call. The usage log surfaces
``prompt_cache_hit_tokens`` / ``prompt_cache_miss_tokens`` so we can confirm it.

Requires DEEPSEEK_API_KEY in .env.
"""

import os
from typing import AsyncIterator

from apps.backend.llm.base_provider import BaseProvider, LLMConfig
from apps.utils.logging import get_logger

logger = get_logger(__name__)

_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekProvider(BaseProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        from openai import AsyncOpenAI, OpenAI

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise KeyError("DEEPSEEK_API_KEY not set in .env")

        self._client = OpenAI(api_key=api_key, base_url=_DEEPSEEK_BASE_URL)
        # Async client used by stream() so the FastAPI event loop is never blocked
        # (the sync call() blocks it, serializing otherwise-parallel section requests).
        self._aclient = AsyncOpenAI(api_key=api_key, base_url=_DEEPSEEK_BASE_URL)

    def _build_params(self, system_prompt: str, user_prompt: str) -> dict:
        """Assemble the Chat Completions params shared by call() and stream()."""
        from openai.types.chat import ChatCompletionMessageParam

        thinking_on = self.config.thinking
        logger.debug(
            "DeepSeekProvider calling model=%s thinking=%s temperature=%s max_tokens=%s",
            self.config.model,
            thinking_on,
            "n/a (thinking)" if thinking_on else self.config.temperature,
            self.config.max_tokens,
        )

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        params: dict = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            # `thinking` is DeepSeek-specific → extra_body. `reasoning_effort` is a
            # native OpenAI param and must stay top-level (nesting it inside
            # `thinking` gets silently stripped).
            "extra_body": {"thinking": {"type": "enabled" if thinking_on else "disabled"}},
        }
        if thinking_on:
            params["reasoning_effort"] = self.config.reasoning_effort
        else:
            # thinking mode silently ignores temperature, so only send it when off.
            params["temperature"] = self.config.temperature
        return params

    def call(self, system_prompt: str, user_prompt: str) -> str:
        import openai

        params = self._build_params(system_prompt, user_prompt)

        try:
            response = self._client.chat.completions.create(**params)
        except openai.APIError as e:
            # Base class for every API failure (connection, timeout, rate-limit,
            # 4xx/5xx). Code bugs deliberately propagate unmasked.
            status = getattr(e, "status_code", None)
            logger.error(
                "DeepSeek API error (model=%s, status=%s): %s",
                self.config.model,
                status,
                e,
                exc_info=True,
            )
            raise

        self._log_usage(response)
        return response.choices[0].message.content or ""

    async def stream(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncIterator[str]:
        """Yield content deltas as the model generates them.

        Uses the async client so the FastAPI event loop stays free — this is what
        lets the per-section requests actually run concurrently. ``include_usage``
        makes DeepSeek emit a final usage-only chunk so the cache-hit/miss log line
        still appears in streaming mode.
        """
        import openai

        params = self._build_params(system_prompt, user_prompt)
        params["stream"] = True
        params["stream_options"] = {"include_usage": True}

        try:
            stream = await self._aclient.chat.completions.create(**params)
            async for chunk in stream:
                # The terminal usage-only chunk carries no choices.
                if chunk.usage is not None:
                    self._log_usage(chunk)
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except openai.APIError as e:
            status = getattr(e, "status_code", None)
            logger.error(
                "DeepSeek streaming API error (model=%s, status=%s): %s",
                self.config.model,
                status,
                e,
                exc_info=True,
            )
            raise

    @staticmethod
    def _log_usage(response) -> None:
        """Log token usage — cache hit/miss confirms prefix caching is working."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        details = getattr(usage, "completion_tokens_details", None)
        logger.info(
            "DeepSeek usage: prompt=%s cache_hit=%s cache_miss=%s completion=%s "
            "reasoning=%s total=%s",
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "prompt_cache_hit_tokens", None),
            getattr(usage, "prompt_cache_miss_tokens", None),
            getattr(usage, "completion_tokens", None),
            getattr(details, "reasoning_tokens", None) if details else None,
            getattr(usage, "total_tokens", None),
        )
