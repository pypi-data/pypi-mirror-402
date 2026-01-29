"""Validation command tests."""
# this_file: tests/test_validation.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abersetz import validation
from abersetz.config import AbersetzConfig, Defaults, EngineConfig
from abersetz.engines import EngineError, EngineRequest, EngineResult
from abersetz.validation import validate_engines


@dataclass
class _StubEngine:
    selector: str
    text: str = ""
    should_fail: bool = False
    return_empty: bool = False

    name: str = "stub"
    chunk_size: int | None = None
    html_chunk_size: int | None = None

    def translate(self, request: EngineRequest) -> EngineResult:
        if self.should_fail:
            raise RuntimeError(f"boom:{self.selector}")
        self.text = request.text
        if self.return_empty:
            return EngineResult(text="   ", voc={})
        return EngineResult(text=f"{self.selector}-ok", voc={})

    def chunk_size_for(self, fmt: Any) -> int | None:  # pragma: no cover - unused in tests
        return self.chunk_size


def _build_config() -> AbersetzConfig:
    return AbersetzConfig(
        defaults=Defaults(engine="tr/google"),
        engines={
            "translators": EngineConfig(
                name="translators", options={"providers": ["google", "bing"]}
            ),
            "deep-translator": EngineConfig(
                name="deep-translator", options={"providers": ["deepl"]}
            ),
            "ullm": EngineConfig(
                name="ullm",
                options={
                    "profiles": {
                        "default": {"model": "stub"},
                        "alt": {"model": "stub-alt"},
                    }
                },
            ),
        },
    )


def test_validate_engines_collects_results() -> None:
    config = _build_config()
    created: list[str] = []

    def fake_create_engine(
        selector: str, cfg: AbersetzConfig, *, client: Any | None = None
    ) -> _StubEngine:
        created.append(selector)
        return _StubEngine(selector=selector)

    results = validate_engines(config, create_engine_fn=fake_create_engine)

    assert created == [
        "tr/bing",
        "tr/google",
        "dt/deepl",
        "ll/alt",
        "ll/default",
    ]
    assert [result.selector for result in results] == created
    assert all(result.success for result in results)
    assert all(result.translation.endswith("-ok") for result in results)
    assert all(result.error is None for result in results)
    assert {result.translation for result in results} == {
        "tr/bing-ok",
        "tr/google-ok",
        "dt/deepl-ok",
        "ll/alt-ok",
        "ll/default-ok",
    }


def test_validate_engines_handles_failures() -> None:
    config = _build_config()

    def fake_create_engine(
        selector: str, cfg: AbersetzConfig, *, client: Any | None = None
    ) -> _StubEngine:
        if selector == "tr/bing":
            raise EngineError("no config")
        return _StubEngine(selector=selector, should_fail=selector == "ll/alt")

    results = validate_engines(config, create_engine_fn=fake_create_engine)

    failure = {result.selector: result for result in results}
    assert not failure["tr/bing"].success
    assert failure["tr/bing"].error == "EngineError: no config"
    assert failure["tr/bing"].translation == ""

    assert not failure["ll/alt"].success
    assert failure["ll/alt"].error is not None and "boom:ll/alt" in failure["ll/alt"].error
    assert failure["ll/alt"].translation == ""

    assert failure["tr/google"].success
    assert failure["dt/deepl"].success


def test_validate_engines_limits_selectors() -> None:
    config = _build_config()
    captured: list[str] = []

    def fake_create_engine(
        selector: str, cfg: AbersetzConfig, *, client: Any | None = None
    ) -> _StubEngine:
        captured.append(selector)
        return _StubEngine(selector=selector)

    results = validate_engines(
        config,
        selectors=["tr/bing", "ll/default"],
        create_engine_fn=fake_create_engine,
    )

    assert captured == ["tr/bing", "ll/default"]
    assert [result.selector for result in results] == ["tr/bing", "ll/default"]


def test_validate_engines_flags_empty_translations() -> None:
    config = _build_config()

    def fake_create_engine(
        selector: str, cfg: AbersetzConfig, *, client: Any | None = None
    ) -> _StubEngine:
        return _StubEngine(selector=selector, return_empty=True)

    results = validate_engines(config, create_engine_fn=fake_create_engine)

    assert all(not item.success for item in results)
    assert all(item.error == "Empty translation" for item in results)


def test_append_selector_handles_empty_and_duplicates() -> None:
    collected: list[str] = []
    seen: set[str] = set()

    validation._append_selector(collected, seen, None)
    validation._append_selector(collected, seen, "")
    validation._append_selector(collected, seen, "tr/google")
    validation._append_selector(collected, seen, "tr/google")

    assert collected == ["tr/google"]


def test_extract_providers_merges_lists_and_fallback() -> None:
    result = validation._extract_providers(
        {"providers": ["  bing", "google", ""], "provider": "deepl"},
        "providers",
    )
    assert result == ["bing", "google", "deepl"]

    result = validation._extract_providers({"providers": "argos", "provider": "bing"}, "providers")
    assert result == ["argos", "bing"]


def test_selectors_from_config_collects_all_engines() -> None:
    cfg = AbersetzConfig(
        defaults=Defaults(engine="translators/google"),
        engines={
            "translators": EngineConfig(name="translators", options={"providers": ["bing"]}),
            "deep-translator": EngineConfig(name="deep-translator", options={"provider": "deepl"}),
            "hysf": EngineConfig(name="hysf", options={}),
            "ullm": EngineConfig(name="ullm", options={"profiles": "default"}),
        },
    )

    selectors = validation._selectors_from_config(cfg, include_defaults=True)

    assert selectors == [
        "tr/bing",
        "tr/google",
        "dt/deepl",
        "hy",
        "ll",
    ]

    selectors_without_default = validation._selectors_from_config(cfg, include_defaults=False)
    assert "tr/google" not in selectors_without_default
