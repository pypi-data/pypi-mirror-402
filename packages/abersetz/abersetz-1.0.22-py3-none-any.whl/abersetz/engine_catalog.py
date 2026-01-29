"""Engine catalog utilities for abersetz."""
# this_file: src/abersetz/engine_catalog.py

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

ENGINE_FAMILY_SHORT_TO_LONG: dict[str, str] = {
    "tr": "translators",
    "dt": "deep-translator",
    "ll": "ullm",
    "hy": "hysf",
}

ENGINE_FAMILY_LONG_TO_SHORT: dict[str, str] = {
    long: short for short, long in ENGINE_FAMILY_SHORT_TO_LONG.items()
}


def _split_selector(selector: str) -> tuple[str, str | None]:
    base, sep, variant = selector.partition("/")
    base = base.strip()
    if not sep:
        return base, None
    cleaned_variant = variant.strip()
    return base, cleaned_variant or None


def normalize_selector(selector: str | None) -> str | None:
    """Return canonical short selector for supported engine families."""

    if selector is None:
        return None
    trimmed = selector.strip()
    if not trimmed:
        return trimmed
    base, variant = _split_selector(trimmed)
    if not base:
        return trimmed
    base_key = base.lower()
    if base_key in ENGINE_FAMILY_SHORT_TO_LONG:
        short_base = base_key
    elif base_key in ENGINE_FAMILY_LONG_TO_SHORT:
        short_base = ENGINE_FAMILY_LONG_TO_SHORT[base_key]
    else:
        return trimmed
    return f"{short_base}/{variant}" if variant else short_base


def resolve_engine_reference(selector: str) -> tuple[str, str | None]:
    """Resolve selector (short or long) into engine config key and variant."""

    base, variant = _split_selector(selector.strip()) if selector else ("", None)
    base_key = base.lower()
    if base_key in ENGINE_FAMILY_SHORT_TO_LONG:
        return ENGINE_FAMILY_SHORT_TO_LONG[base_key], variant
    if base_key in ENGINE_FAMILY_LONG_TO_SHORT:
        return base_key, variant
    return base, variant


# Provider lists derived from translators README tables
# (see external/translators.txt:1030-1100 for catalogue of public engines)
FREE_TRANSLATOR_PROVIDERS = (
    "google",
    "bing",
    "yandex",
    "argos",
    "apertium",
    "elia",
    "iciba",
    "libre",
    "linguee",
    "myMemory",
    "papago",
    "reverso",
    "tilde",
    "translateCom",
    "translateMe",
    "utibet",
    "youdao",
)

COMMUNITY_TRANSLATOR_PROVIDERS = ("libre",)

PAID_TRANSLATOR_PROVIDERS = (
    "alibaba",
    "baidu",
    "caiyun",
    "cloudTranslation",
    "deepl",
    "hujiang",
    "iflytek",
    "iflyrec",
    "itranslate",
    "judic",
    "languageWire",
    "lingvanex",
    "mglip",
    "mirai",
    "modernMt",
    "niutrans",
    "qqFanyi",
    "qqTranSmart",
    "sogou",
    "sysTran",
    "volcEngine",
    "yeekit",
)

# Deep-translator engines (external/deep-translator.txt modules list)
DEEP_TRANSLATOR_FREE_PROVIDERS = (
    "google",
    "libre",
    "linguee",
    "my_memory",
)
COMMUNITY_DEEP_TRANSLATOR_PROVIDERS = ("libre",)
DEEP_TRANSLATOR_PAID_PROVIDERS = (
    "deepl",
    "microsoft",
    "papago",
)

HYSF_DEFAULT_MODEL = "tencent/Hunyuan-MT-7B"
HYSF_DEFAULT_TEMPERATURE = 0.9


def _filter_available(pool: Iterable[str], allowed: Iterable[str]) -> list[str]:
    pool_set = {item for item in pool}
    ordered: list[str] = []
    for candidate in allowed:
        if candidate in pool_set and candidate not in ordered:
            ordered.append(candidate)
    return ordered


def collect_translator_providers(*, include_paid: bool = False) -> list[str]:
    """Return translator providers available in current environment."""
    try:
        import translators  # type: ignore
    except Exception:
        return []
    pool = translators.translators_pool
    allowed = list(FREE_TRANSLATOR_PROVIDERS)
    if include_paid:
        allowed.extend(PAID_TRANSLATOR_PROVIDERS)
    return _filter_available(pool, allowed)


def collect_deep_translator_providers(*, include_paid: bool = False) -> list[str]:
    """Return deep-translator providers supported by abersetz."""
    pool = list(DEEP_TRANSLATOR_FREE_PROVIDERS)
    if include_paid:
        pool.extend(DEEP_TRANSLATOR_PAID_PROVIDERS)
    seen: set[str] = set()
    ordered: list[str] = []
    for item in pool:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


@dataclass(slots=True)
class EngineEntry:
    """Descriptor for CLI listing."""

    selector: str
    configured: bool
    requires_api_key: bool
    notes: str = ""
