"""
LLM service — single entry point for all BaZi LLM analysis.

Usage:
    from src.llm.llm_service import analyse_bazi, LLMError
    response = analyse_bazi(llm_friendly_data)
"""

from pathlib import Path

from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import OmegaConf

from src.llm.base_provider import LLMConfig, LLMResponse
from src.llm.prompt_builder import PromptBuilder
from src.llm.response_parser import ResponseParser
from src.utils.logging import get_logger

logger = get_logger(__name__)

_CONFIG_DIR = str(Path(__file__).parent.parent.parent / "config")


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
        cfg, "templates.user", default="prompts/life_overview_prompt.jinja"
    )

    return config, system_template, user_template


def _make_provider(config: LLMConfig):
    """Factory — lazy imports so uninstalled SDKs don't crash at startup."""
    try:
        if config.provider == "gemini":
            from src.llm.providers.gemini import GeminiProvider

            return GeminiProvider(config)
        elif config.provider == "claude":
            from src.llm.providers.claude import ClaudeProvider

            return ClaudeProvider(config)
        elif config.provider == "huggingface":
            from src.llm.providers.huggingface import HuggingFaceProvider

            return HuggingFaceProvider(config)
        else:
            raise LLMError(f"Unknown provider: '{config.provider}'")
    except KeyError as e:
        raise LLMError(str(e)) from e


def analyse_bazi(llm_data: dict) -> LLMResponse:
    """
    Run BaZi LLM analysis using the configured provider.

    Args:
        llm_data: Output of AstroDataLLMFormatter.format_for_llm()

    Returns:
        LLMResponse with life_overview, romance, career, and raw_text

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
# python -m src.llm.llm_service
if __name__ == "__main__":
    from datetime import datetime

    from dotenv import load_dotenv

    load_dotenv()

    from src.utils.logging import configure_logging

    configure_logging()

    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
    from src.services.astronomer_data_aggregator import AstroDataAggregator
    from src.services.astronomer_data_llm_formatter import AstroDataLLMFormatter

    # python -m src.llm.llm_service

    # --- Choose subject ---
    # Desmond
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    latitude, longitude, gender = 1.3253, 103.808053, 1

    # Corinne
    # datetime_birthday = datetime(1987, 6, 3, 12, 6, 0)
    # latitude, longitude, gender = 1.4759, 103.808053, 0

    # Lara
    # datetime_birthday = datetime(2025, 7, 31, 9, 10, 0)
    # latitude, longitude, gender = 1.3253, 103.808053, 0

    tst_birthday, _ = get_true_solar_time(datetime_birthday, latitude, longitude)
    lunar_birthday = tst_birthday.getLunar()

    # Collect & format
    raw_data = AstroDataAggregator().collect_data(
        lunar_birthday,
        birth_datetime=datetime_birthday,
        latitude=latitude,
        longitude=longitude,
        gender=gender,
    )
    llm_friendly_data = AstroDataLLMFormatter(raw_data).format_for_llm()

    logger.info("=== Running LLM Analysis ===")
    result = analyse_bazi(llm_friendly_data)

    ov = result.life_overview
    logger.info(
        "--- Life Overview ---\npoem: %d chars | self_verification: %d | core_identity: %d | life_so_far: %d | defining_moments: %d | the_future: %d | destiny_balance_sheet: %d | living_in_alignment: %d",
        len(ov.poem),
        len(ov.self_verification),
        len(ov.core_identity),
        len(ov.life_so_far),
        len(ov.defining_moments),
        len(ov.the_future),
        len(ov.destiny_balance_sheet),
        len(ov.living_in_alignment),
    )
    logger.info("--- Romance ---\n%s", result.romance)
    logger.info("--- Career ---\n%s", result.career)
    logger.info("--- Raw Text ---\n%s", result.raw_text)
