"""Tests for engine selector alias utilities."""
# this_file: tests/test_engine_catalog.py

from __future__ import annotations

import builtins
import sys
from types import SimpleNamespace
from typing import Any

import pytest

from abersetz.engine_catalog import (
    _filter_available,
    collect_deep_translator_providers,
    collect_translator_providers,
    normalize_selector,
    resolve_engine_reference,
)


def test_normalize_selector_converts_long_to_short() -> None:
    assert normalize_selector("translators/google") == "tr/google"


def test_normalize_selector_is_idempotent() -> None:
    assert normalize_selector("tr/google") == "tr/google"


def test_normalize_selector_preserves_unknowns() -> None:
    assert normalize_selector("custom-engine") == "custom-engine"


def test_normalize_selector_returns_none_for_none() -> None:
    assert normalize_selector(None) is None


def test_normalize_selector_handles_blank_input() -> None:
    assert normalize_selector("   ") == ""


def test_normalize_selector_handles_missing_base() -> None:
    assert normalize_selector("/bing") == "/bing"


def test_resolve_engine_reference_handles_short_alias() -> None:
    base, variant = resolve_engine_reference("tr/google")
    assert base == "translators"
    assert variant == "google"


def test_resolve_engine_reference_handles_long_selector() -> None:
    base, variant = resolve_engine_reference("deep-translator/deepl")
    assert base == "deep-translator"
    assert variant == "deepl"


def test_resolve_engine_reference_handles_base_only_alias() -> None:
    base, variant = resolve_engine_reference("hy")
    assert base == "hysf"
    assert variant is None


def test_filter_available_when_allowed_duplicates_then_dedupes() -> None:
    ordered = _filter_available(["google", "bing"], ["bing", "google", "bing"])
    assert ordered == ["bing", "google"]


def test_collect_translator_providers_when_import_fails_then_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any):
        if name == "translators":
            raise RuntimeError("translators unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    math_module = __import__("math")
    assert math_module.__name__ == "math", "Fallback importer must keep stdlib imports working"
    assert collect_translator_providers() == []


def test_collect_translator_providers_when_paid_requested_then_keeps_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = SimpleNamespace(translators_pool=["deepl", "google", "bing", "unknown"])
    monkeypatch.setitem(sys.modules, "translators", module)
    providers = collect_translator_providers(include_paid=True)
    assert providers == ["google", "bing", "deepl"]


def test_collect_deep_translator_providers_include_paid_appends_once() -> None:
    free_only = collect_deep_translator_providers(include_paid=False)
    include_paid = collect_deep_translator_providers(include_paid=True)

    assert free_only == ["google", "libre", "linguee", "my_memory"]
    assert include_paid[: len(free_only)] == free_only
    assert include_paid[-3:] == ["deepl", "microsoft", "papago"]
    assert len(include_paid) == len(set(include_paid))
