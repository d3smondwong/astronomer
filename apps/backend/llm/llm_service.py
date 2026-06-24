"""
LLM service — single entry point for all BaZi LLM analysis.

Usage:
    from apps.backend.llm.llm_service import llm_analyse_bazi, LLMError
    response = llm_analyse_bazi(natal_chart_data)
"""

from pathlib import Path

from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import OmegaConf

from apps.backend.llm.base_provider import InsightsResponse, LLMConfig
from apps.backend.llm.prompt_builder import PromptBuilder
from apps.backend.llm.response_parser import ResponseParser
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Repo-root config/ holds llm_config.yaml: llm -> backend -> apps -> root
_CONFIG_DIR = str(Path(__file__).parent.parent.parent.parent / "config")


class LLMError(Exception):
    """Raised for all recoverable LLM integration failures."""


def _load_config() -> tuple[LLMConfig, str, str]:
    """
    Load llm_config.yaml via the Hydra Compose API and return
    (LLMConfig, system_template, user_template).

    GlobalHydra is cleared before each call so this is safe to call
    repeatedly inside a Streamlit session (which re-runs on every interaction).
    """
    try:
        GlobalHydra.instance().clear()
        with initialize_config_dir(config_dir=_CONFIG_DIR, version_base=None):
            cfg = compose(config_name="llm_config")
    except Exception as e:
        raise LLMError(f"Failed to load llm_config.yaml: {e}") from e

    active = cfg.get("active_provider")
    if not active:
        raise LLMError("llm_config.yaml missing 'active_provider'")

    logger.debug("Active LLM provider: %s", active)

    provider_cfg = cfg.get("providers", {}).get(active)
    if not provider_cfg:
        raise LLMError(f"No config found for provider '{active}' in llm_config.yaml")

    config = LLMConfig(
        provider=active,
        model=provider_cfg.model,
        temperature=provider_cfg.temperature,
        max_tokens=provider_cfg.max_tokens,
        stream=provider_cfg.get("stream", False),
    )

    system_template = OmegaConf.select(
        cfg, "templates.system", default="prompts/system_prompt.jinja"
    )
    user_template = OmegaConf.select(
        cfg, "templates.user", default="prompts/insights_prompt.jinja"
    )

    return config, system_template, user_template


def _make_provider(config: LLMConfig):
    """Factory — lazy imports so uninstalled SDKs don't crash at startup."""
    try:
        if config.provider == "gemini":
            from apps.backend.llm.providers.gemini import GeminiProvider

            return GeminiProvider(config)
        elif config.provider == "claude":
            from apps.backend.llm.providers.claude import ClaudeProvider

            return ClaudeProvider(config)
        elif config.provider == "huggingface":
            from apps.backend.llm.providers.huggingface import HuggingFaceProvider

            return HuggingFaceProvider(config)
        elif config.provider == "deepseek":
            from apps.backend.llm.providers.deepseek import DeepSeekProvider

            return DeepSeekProvider(config)
        else:
            raise LLMError(f"Unknown provider: '{config.provider}'")
    except KeyError as e:
        raise LLMError(str(e)) from e


def get_active_model() -> str:
    """Return '<provider>/<model>' for the currently configured provider."""
    config, _, _ = _load_config()
    return f"{config.provider}/{config.model}"


def llm_analyse_bazi(llm_data: dict) -> InsightsResponse:
    """
    Run BaZi LLM analysis using the configured provider.

    Args:
        llm_data: The natal chart dict from the orchestrator
            (calculate_natal_chart output) — Chinese-keyed.

    Returns:
        InsightsResponse with the personality contract and raw_text

    Raises:
        LLMError: For any configuration, API key, or network failure
    """
    config, system_template, user_template = _load_config()

    logger.info("Calling %s / %s for BaZi analysis", config.provider, config.model)

    provider = _make_provider(config)
    system_prompt, user_prompt = PromptBuilder(system_template, user_template).build(
        llm_data
    )

    try:
        raw_text = provider.call(system_prompt, user_prompt)
    except LLMError:
        raise
    except Exception as e:
        logger.error("LLM call failed: %s", e, exc_info=True)
        raise LLMError(f"{config.provider} API error: {e}") from e

    logger.info(
        "LLM response received (%d chars) from %s / %s",
        len(raw_text),
        config.provider,
        config.model,
    )

    return ResponseParser().parse(raw_text)


# --- EXECUTION ---
# python -m apps.backend.llm.llm_service
if __name__ == "__main__":
    from datetime import datetime

    from dotenv import load_dotenv

    load_dotenv()

    from src.utils.logging import configure_logging

    configure_logging()

    from apps.backend.orchestrator.astronomer_data_orchestrator import (
        calculate_natal_chart,
    )

    # --- Sample subject (Desmond) ---
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    latitude, longitude, gender = 1.3253, 103.808053, 1

    chart = calculate_natal_chart(
        birth_datetime=datetime_birthday,
        latitude=latitude,
        longitude=longitude,
        gender=gender,
        use_solar_time_correction=True,
    )

    logger.info("=== Running LLM Analysis ===")
    result = llm_analyse_bazi(chart)

    p = result.personality
    logger.info(
        "--- Personality ---\narchetype: %s | element: %s | traits: %d | strengths: %d | areas: %d | colors: %d | numbers: %d",
        p.archetype,
        p.element,
        len(p.key_traits),
        len(p.strengths),
        len(p.areas_to_note),
        len(p.lucky_colors),
        len(p.lucky_numbers),
    )
    logger.info("--- Raw Text ---\n%s", result.raw_text)
