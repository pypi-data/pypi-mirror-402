"""Runtime engine validation utilities."""
# this_file: src/abersetz/validation.py

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from time import perf_counter

from loguru import logger

from .config import AbersetzConfig, load_config
from .engine_catalog import normalize_selector
from .engines import EngineError, EngineRequest, create_engine


@dataclass(slots=True)
class ValidationResult:
    """Outcome of validating a single engine selector."""

    selector: str
    success: bool
    translation: str
    error: str | None
    latency: float


def _append_selector(collection: list[str], seen: set[str], selector: str | None) -> None:
    if not selector:
        return
    if selector in seen:
        return
    seen.add(selector)
    collection.append(selector)


def _extract_providers(options: dict[str, object], key: str) -> list[str]:
    raw = options.get(key)
    if isinstance(raw, Sequence) and not isinstance(raw, str | bytes):
        values = [str(item).strip() for item in raw if str(item).strip()]
        result = sorted(values, key=str.lower)
    elif raw:
        value = str(raw).strip()
        result = [value] if value else []
    else:
        result = []
    fallback = options.get("provider")
    if fallback:
        fallback_value = str(fallback).strip()
        if fallback_value and fallback_value not in result:
            result.append(fallback_value)
    return result


def _selector_sort_key(selector: str) -> tuple[int, str]:
    base = selector.split("/", 1)[0]
    order = {"tr": 0, "dt": 1, "hy": 2, "ll": 3}
    return (order.get(base, 99), selector)


def _selectors_from_config(config: AbersetzConfig, include_defaults: bool) -> list[str]:
    selectors: set[str] = set()

    if include_defaults and config.defaults.engine:
        normalized = normalize_selector(config.defaults.engine) or config.defaults.engine
        if normalized:
            selectors.add(normalized)

    translators_cfg = config.engines.get("translators")
    if translators_cfg:
        for provider in _extract_providers(translators_cfg.options, "providers"):
            normalized = normalize_selector(f"translators/{provider}") or f"translators/{provider}"
            selectors.add(normalized)

    deep_cfg = config.engines.get("deep-translator")
    if deep_cfg:
        for provider in _extract_providers(deep_cfg.options, "providers"):
            normalized = (
                normalize_selector(f"deep-translator/{provider}") or f"deep-translator/{provider}"
            )
            selectors.add(normalized)

    if config.engines.get("hysf"):
        selectors.add(normalize_selector("hysf") or "hysf")

    ullm_cfg = config.engines.get("ullm")
    if ullm_cfg:
        profiles = ullm_cfg.options.get("profiles")
        if isinstance(profiles, dict):
            for profile in sorted(profiles):
                normalized = normalize_selector(f"ullm/{profile}") or f"ullm/{profile}"
                selectors.add(normalized)
        else:
            selectors.add(normalize_selector("ullm") or "ullm")

    return sorted(selectors, key=_selector_sort_key)


def _ensure_engine_request(sample_text: str, source_lang: str, target_lang: str) -> EngineRequest:
    return EngineRequest(
        text=sample_text,
        source_lang=source_lang,
        target_lang=target_lang,
        is_html=False,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )


def validate_engines(
    config: AbersetzConfig | None = None,
    *,
    selectors: Iterable[str] | None = None,
    sample_text: str = "Hello, world!",
    source_lang: str = "auto",
    target_lang: str = "es",
    client: object | None = None,
    create_engine_fn: Callable[..., object] | None = None,
    include_defaults: bool = True,
) -> list[ValidationResult]:
    """Validate configured engines by performing a tiny translation."""

    cfg = config or load_config()
    factory = create_engine_fn or create_engine

    if selectors is None:
        candidate_selectors = _selectors_from_config(cfg, include_defaults)
    else:
        candidate_selectors = []
        seen: set[str] = set()
        for selector in selectors:
            normalized = normalize_selector(selector) or selector
            _append_selector(candidate_selectors, seen, normalized)

    request = _ensure_engine_request(sample_text, source_lang, target_lang)
    results: list[ValidationResult] = []

    for selector in candidate_selectors:
        started = perf_counter()
        try:
            engine = factory(selector, cfg, client=client)
            engine_result = engine.translate(request)  # type: ignore[attr-defined]
            translation = engine_result.text.strip()
            success = bool(translation)
            error: str | None = None if success else "Empty translation"
        except EngineError as exc:
            translation = ""
            success = False
            error = f"EngineError: {exc}"
        except Exception as exc:  # pragma: no cover - unexpected errors
            translation = ""
            success = False
            error = f"{exc.__class__.__name__}: {exc}"
        latency = perf_counter() - started
        logger.debug("Validated %s: success=%s latency=%.3fs", selector, success, latency)
        results.append(
            ValidationResult(
                selector=selector,
                success=success,
                translation=translation if success else "",
                error=error,
                latency=latency,
            )
        )

    return results


__all__ = ["ValidationResult", "validate_engines"]
