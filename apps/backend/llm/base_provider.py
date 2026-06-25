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
class InsightsReport:
    """The multi-section insight report.

    sections:       section key (e.g. "personality") -> narrative prose string.
    raw_by_section: section key -> the raw LLM response for that section (for audit).
    """

    sections: dict[str, str] = field(default_factory=dict)
    raw_by_section: dict[str, str] = field(default_factory=dict)


class BaseProvider(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def call(self, system_prompt: str, user_prompt: str) -> str:
        """Send the prompts to the LLM and return the raw text response."""
        ...
