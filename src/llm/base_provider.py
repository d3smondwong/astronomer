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
class LifeOverview:
    poem: str = ""
    self_verification: str = ""
    core_identity: str = ""
    life_so_far: str = ""
    defining_moments: str = ""
    the_future: str = ""
    destiny_balance_sheet: str = ""
    living_in_alignment: str = ""


@dataclass
class LLMResponse:
    life_overview: LifeOverview
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
