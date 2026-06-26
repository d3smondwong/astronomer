"""
Abstract base class and shared dataclasses for all LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int
    stream: bool = False
    # Reasoning controls — honoured by providers whose models support a thinking
    # mode (e.g. DeepSeek v4). Ignored by providers that don't.
    thinking: bool = False
    reasoning_effort: str = "high"


@dataclass
class InsightsReport:
    """The multi-section insight report.

    sections:       section key (e.g. "personality") -> the section payload: a
                    narrative prose string, or a structured groups object (dict)
                    for sections that define categories (e.g. "career").
    raw_by_section: section key -> the raw LLM response for that section (for audit).
    """

    sections: dict[str, Any] = field(default_factory=dict)
    raw_by_section: dict[str, str] = field(default_factory=dict)


class BaseProvider(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def call(self, system_prompt: str, user_prompt: str) -> str:
        """Send the prompts to the LLM and return the raw text response."""
        ...
