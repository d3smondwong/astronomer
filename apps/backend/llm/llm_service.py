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

from apps.backend.llm.base_provider import InsightsReport, LLMConfig
from apps.backend.llm.prompt_builder import PromptBuilder
from apps.backend.llm.response_parser import ResponseParser
from apps.backend.llm.section_registry import SECTION_REGISTRY
from apps.utils.logging import get_logger

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
        thinking=provider_cfg.get("thinking", False),
        reasoning_effort=provider_cfg.get("reasoning_effort", "high"),
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


def llm_analyse_bazi(llm_data: dict) -> InsightsReport:
    """
    Run the multi-section BaZi LLM analysis using the configured provider.

    Makes one LLM call per section in SECTION_REGISTRY (personality, family,
    romance, career, wealth, health), passing the full chart each time and
    steering focus via the section's guidance/emphasis. A failure in one
    section is logged and skipped so the rest of the report still returns.

    Args:
        llm_data: The natal chart dict from the orchestrator
            (calculate_natal_chart output) — Chinese-keyed.

    Returns:
        InsightsReport: section key -> narrative prose (+ raw_by_section).

    Raises:
        LLMError: For configuration or API-key failures (raised before any
            section runs). Per-section network/parse failures degrade gracefully.
    """
    config, system_template, user_template = _load_config()

    logger.info(
        "Calling %s / %s for BaZi analysis across %d sections",
        config.provider,
        config.model,
        len(SECTION_REGISTRY),
    )

    provider = _make_provider(config)
    builder = PromptBuilder(system_template, user_template)
    parser = ResponseParser()

    report = InsightsReport()

    for section in SECTION_REGISTRY:
        system_prompt, user_prompt = builder.build(section, llm_data)
        try:
            raw_text = provider.call(system_prompt, user_prompt)
        except Exception as e:
            logger.error(
                "LLM call failed for section '%s': %s", section.key, e, exc_info=True
            )
            report.sections[section.key] = ""
            report.raw_by_section[section.key] = ""
            continue

        logger.info(
            "Section '%s' received (%d chars) from %s / %s",
            section.key,
            len(raw_text),
            config.provider,
            config.model,
        )
        report.raw_by_section[section.key] = raw_text
        report.sections[section.key] = parser.parse_section(
            section.key, raw_text, structured=bool(section.categories)
        )

    return report


def llm_analyse_section(llm_data: dict, section_key: str) -> str | dict:
    """
    Generate a single insight section — used for progressive/parallel loading
    so the frontend can render each section as soon as it is ready.

    Args:
        llm_data:    The natal chart dict from the orchestrator.
        section_key: One of the keys in SECTION_REGISTRY (e.g. "personality").

    Returns:
        The narrative prose for that section.

    Raises:
        LLMError: Unknown section key, config/API-key failure, or LLM call failure.
    """
    section = next((s for s in SECTION_REGISTRY if s.key == section_key), None)
    if section is None:
        raise LLMError(f"Unknown insight section: '{section_key}'")

    config, system_template, user_template = _load_config()
    logger.info(
        "Calling %s / %s for insight section '%s'",
        config.provider,
        config.model,
        section_key,
    )

    provider = _make_provider(config)
    system_prompt, user_prompt = PromptBuilder(system_template, user_template).build(
        section, llm_data
    )

    try:
        raw_text = provider.call(system_prompt, user_prompt)
    except LLMError:
        raise
    except Exception as e:
        logger.error("LLM call failed for section '%s': %s", section_key, e, exc_info=True)
        raise LLMError(f"{config.provider} API error: {e}") from e

    logger.info("Section '%s' received (%d chars)", section_key, len(raw_text))
    return ResponseParser().parse_section(
        section.key, raw_text, structured=bool(section.categories)
    )


# --- EXECUTION ---
# Run ONE section only (saves tokens while iterating on a single prompt):
#   python -m apps.backend.llm.llm_service              # defaults to "career"
#   SECTION=wealth python -m apps.backend.llm.llm_service
if __name__ == "__main__":
    import json as _json
    import os
    from datetime import datetime

    from dotenv import load_dotenv

    load_dotenv()

    from apps.utils.logging import configure_logging

    configure_logging()

    from apps.backend.orchestrator.astronomer_data_orchestrator import (
        calculate_natal_chart,
    )

    section_key = os.environ.get("SECTION", "career")

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

    section = next((s for s in SECTION_REGISTRY if s.key == section_key), None)
    if section is None:
        raise SystemExit(
            f"Unknown section '{section_key}'. Choose from: "
            f"{', '.join(s.key for s in SECTION_REGISTRY)}"
        )

    logger.info("=== Running LLM Analysis — section '%s' only ===", section_key)

    config, system_template, user_template = _load_config()
    provider = _make_provider(config)
    system_prompt, user_prompt = PromptBuilder(system_template, user_template).build(
        section, chart
    )
    raw_text = provider.call(system_prompt, user_prompt)

    # Pretty-print if it parses as JSON, otherwise show the raw text verbatim.
    try:
        pretty = _json.dumps(_json.loads(raw_text), ensure_ascii=False, indent=2)
    except _json.JSONDecodeError:
        pretty = raw_text

    logger.info(
        "\n===== %s (%s) — %d chars =====\n%s",
        section.title,
        section.key,
        len(raw_text),
        pretty or "[empty]",
    )
