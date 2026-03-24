"""
Abstract base class and shared dataclasses for all LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int
    stream: bool = False


@dataclass
class LLMResponse:
    life_overview: str
    romance: str
    career: str
    raw_text: str


class BaseProvider(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def call(self, system_prompt: str, user_prompt: str) -> str:
        """Send the prompts to the LLM and return the raw text response."""
        ...
