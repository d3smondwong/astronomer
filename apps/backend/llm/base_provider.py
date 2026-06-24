"""
Abstract base class and shared dataclasses for all LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int
    stream: bool = False


@dataclass
class Personality:
    """The personality section of the Insights contract."""

    archetype: str = ""
    element: str = ""
    key_traits: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    areas_to_note: list[str] = field(default_factory=list)
    lucky_colors: list[str] = field(default_factory=list)
    lucky_numbers: list[str] = field(default_factory=list)


@dataclass
class InsightsResponse:
    personality: Personality
    raw_text: str


class BaseProvider(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def call(self, system_prompt: str, user_prompt: str) -> str:
        """Send the prompts to the LLM and return the raw text response."""
        ...
