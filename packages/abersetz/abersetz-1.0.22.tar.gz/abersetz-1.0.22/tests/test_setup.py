"""Setup wizard validation integration tests."""
# this_file: tests/test_setup.py

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import httpx
import pytest

from abersetz.config import AbersetzConfig
from abersetz.engine_catalog import normalize_selector
from abersetz.setup import (
    DiscoveredProvider,
    EngineConfig,
    SetupWizard,
    _select_default_engine,
    setup_command,
)


def _stub_phase(*args: Any, **kwargs: Any) -> None:  # pragma: no cover - helper
    return None


class _StubProgress:
    def __enter__(self) -> _StubProgress:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def add_task(self, description: str, total: int) -> str:
        return "task"

    def update(self, task: str, advance: int) -> None:
        return None


def test_setup_wizard_triggers_validation(monkeypatch) -> None:
    config = AbersetzConfig()
    wizard = SetupWizard(non_interactive=True)

    monkeypatch.setattr(SetupWizard, "_discover_providers", _stub_phase)
    monkeypatch.setattr(SetupWizard, "_test_endpoints", _stub_phase)
    monkeypatch.setattr(SetupWizard, "_display_results", _stub_phase)
    monkeypatch.setattr(SetupWizard, "_generate_config", lambda self: config)
    monkeypatch.setattr("abersetz.setup.save_config", lambda cfg: None)

    captured: list[AbersetzConfig] = []
    monkeypatch.setattr(SetupWizard, "_validate_config", lambda self, cfg: captured.append(cfg))

    assert wizard.run() is True
    assert captured == [config]


def test_setup_wizard_skips_validation_when_no_config(monkeypatch) -> None:
    wizard = SetupWizard(non_interactive=True)

    monkeypatch.setattr(SetupWizard, "_discover_providers", _stub_phase)
    monkeypatch.setattr(SetupWizard, "_test_endpoints", _stub_phase)
    monkeypatch.setattr(SetupWizard, "_display_results", _stub_phase)
    monkeypatch.setattr(SetupWizard, "_generate_config", lambda self: None)

    called = []
    monkeypatch.setattr(SetupWizard, "_validate_config", lambda self, cfg: called.append(cfg))

    assert wizard.run() is False
    assert called == []


def test_discover_providers_adds_pricing_hint(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "token")
    wizard = SetupWizard(non_interactive=True)
    wizard._discover_providers()
    assert wizard.discovered_providers
    assert wizard.discovered_providers[0].pricing_hint != "Unknown"


def test_discover_providers_includes_deepl_engine_mapping(monkeypatch) -> None:
    monkeypatch.setenv("DEEPL_API_KEY", "token")

    wizard = SetupWizard(non_interactive=True)
    wizard._discover_providers()

    deepl_provider = next(p for p in wizard.discovered_providers if p.name == "deepl")
    expected = str(normalize_selector("deep-translator/deepl"))

    assert expected in deepl_provider.engine_names


def test_display_results_shows_pricing_column(monkeypatch) -> None:
    import io

    from rich.console import Console

    output = io.StringIO()
    monkeypatch.setattr("abersetz.setup.console", Console(file=output, force_terminal=True))

    wizard = SetupWizard(non_interactive=True)
    wizard.discovered_providers = [
        DiscoveredProvider(
            name="google",
            api_key_env="GOOGLE_API_KEY",
            is_available=True,
            engine_names=["tr/google"],
            model_count=1,
            pricing_hint="Free",
        )
    ]

    wizard._display_results()

    rendered = output.getvalue()
    assert "Pricing" in rendered
    assert "Free" in rendered


def test_generate_config_builds_engines(monkeypatch) -> None:
    wizard = SetupWizard(non_interactive=True)
    wizard.discovered_providers = [
        DiscoveredProvider(
            name="google",
            api_key_env="GOOGLE_API_KEY",
            is_available=True,
            engine_names=["tr/google"],
            pricing_hint="Community",
        ),
        DiscoveredProvider(
            name="deepl",
            api_key_env="DEEPL_API_KEY",
            is_available=True,
            engine_names=["dt/deepl"],
        ),
        DiscoveredProvider(
            name="siliconflow",
            api_key_env="SILICONFLOW_API_KEY",
            base_url="https://api.siliconflow.com/v1",
            is_available=True,
            engine_names=["hy", "ll/default"],
        ),
    ]

    config = wizard._generate_config()

    assert config is not None
    assert config.engines["translators"].options["provider"] == "google"
    assert "deepl" in config.engines["deep-translator"].options["providers"]
    assert "hysf" in config.engines
    default_engine = normalize_selector(config.defaults.engine) or config.defaults.engine
    assert default_engine in {"tr/google", "dt/deepl", "hy", "ll/default"}


def test_generate_config_excludes_community_providers_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wizard = SetupWizard(non_interactive=True)
    wizard.discovered_providers = [
        DiscoveredProvider(name="google", api_key_env="GOOGLE_API_KEY", is_available=True)
    ]

    monkeypatch.setattr(
        "abersetz.setup.collect_translator_providers",
        lambda include_paid=False: ["google", "libre"],
    )
    monkeypatch.setattr(
        "abersetz.setup.collect_deep_translator_providers",
        lambda include_paid=False: ["google", "libre"],
    )

    config = wizard._generate_config()

    assert config is not None
    translators = config.engines["translators"].options["providers"]
    deep = config.engines["deep-translator"].options["providers"]
    assert "libre" not in translators
    assert "libre" not in deep


def test_generate_config_includes_community_providers_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wizard = SetupWizard(non_interactive=True, include_community=True)
    wizard.discovered_providers = [
        DiscoveredProvider(name="google", api_key_env="GOOGLE_API_KEY", is_available=True)
    ]

    monkeypatch.setattr(
        "abersetz.setup.collect_translator_providers",
        lambda include_paid=False: ["google", "libre"],
    )
    monkeypatch.setattr(
        "abersetz.setup.collect_deep_translator_providers",
        lambda include_paid=False: ["google", "libre"],
    )

    config = wizard._generate_config()

    assert config is not None
    translators = config.engines["translators"].options["providers"]
    deep = config.engines["deep-translator"].options["providers"]
    assert "libre" in translators
    assert "libre" in deep


def test_generate_config_prefers_hysf_when_translators_unavailable(monkeypatch) -> None:
    wizard = SetupWizard(non_interactive=True)
    wizard.discovered_providers = [
        DiscoveredProvider(
            name="siliconflow",
            api_key_env="SILICONFLOW_API_KEY",
            base_url="https://api.siliconflow.com/v1",
            is_available=True,
        )
    ]

    monkeypatch.setattr(
        "abersetz.setup.collect_translator_providers", lambda include_paid=False: []
    )
    monkeypatch.setattr(
        "abersetz.setup.collect_deep_translator_providers", lambda include_paid=False: []
    )
    monkeypatch.setattr("abersetz.setup.FREE_TRANSLATOR_PROVIDERS", [])
    monkeypatch.setattr("abersetz.setup.DEEP_TRANSLATOR_FREE_PROVIDERS", [])

    config = wizard._generate_config()

    assert config is not None
    assert "hysf" in config.engines
    default_engine = normalize_selector(config.defaults.engine) or config.defaults.engine
    assert default_engine == "hy"


def test_generate_config_defaults_to_ullm_when_only_openai(monkeypatch) -> None:
    wizard = SetupWizard(non_interactive=True)
    wizard.discovered_providers = [
        DiscoveredProvider(
            name="openai",
            api_key_env="OPENAI_API_KEY",
            is_available=True,
        )
    ]

    monkeypatch.setattr(
        "abersetz.setup.collect_translator_providers", lambda include_paid=False: []
    )
    monkeypatch.setattr(
        "abersetz.setup.collect_deep_translator_providers", lambda include_paid=False: []
    )
    monkeypatch.setattr("abersetz.setup.FREE_TRANSLATOR_PROVIDERS", [])
    monkeypatch.setattr("abersetz.setup.DEEP_TRANSLATOR_FREE_PROVIDERS", [])

    config = wizard._generate_config()

    assert config is not None
    assert "ullm" in config.engines
    assert normalize_selector(config.defaults.engine) == "ll/default"


def test_test_single_endpoint_success(monkeypatch) -> None:
    class _DummyResponse:
        status_code = 200

        @staticmethod
        def json() -> dict[str, list[int]]:
            return {"data": [1, 2, 3]}

    class _DummyClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            return None

        def __enter__(self) -> _DummyClient:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            assert "Authorization" in headers
            return _DummyResponse()

    monkeypatch.setattr(httpx, "Client", _DummyClient)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is True
    assert provider.model_count == 3
    assert provider.error is None


def test_test_single_endpoint_parses_list_payload(monkeypatch) -> None:
    class _ListResponse:
        status_code = 200

        @staticmethod
        def json() -> list[int]:
            return [1, 2, 3, 4]

    class _Client:
        def __enter__(self) -> _Client:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            assert headers["Authorization"].startswith("Bearer ")
            return _ListResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(httpx, "Client", lambda *_, **__: _Client())

    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is True
    assert provider.model_count == 4


def test_test_single_endpoint_logs_verbose_status(monkeypatch) -> None:
    from loguru import logger

    class _Response:
        status_code = 200

        @staticmethod
        def json() -> dict[str, list[int]]:
            return {"data": [1, 2]}

    class _Client:
        def __enter__(self) -> _Client:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            return _Response()

    messages: list[str] = []
    token = logger.add(lambda message: messages.append(str(message)), level="DEBUG")
    try:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setattr(httpx, "Client", lambda *_, **__: _Client())

        provider = DiscoveredProvider(
            name="openai",
            api_key_env="OPENAI_API_KEY",
            base_url="https://api.openai.com/v1",
        )

        SetupWizard(non_interactive=True, verbose=True)._test_single_endpoint(provider)
    finally:
        logger.remove(token)

    assert provider.is_available is True
    assert provider.model_count == 2
    assert any("✓ openai" in message for message in messages)


def test_test_single_endpoint_timeout(monkeypatch) -> None:
    class _TimeoutClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            return None

        def __enter__(self) -> _TimeoutClient:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "Client", _TimeoutClient)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is False
    assert provider.error == "Timeout"


def test_test_single_endpoint_http_error(monkeypatch) -> None:
    class _HttpErrorResponse:
        status_code = 503

        @staticmethod
        def json() -> dict[str, list[int]]:  # pragma: no cover - not called
            return {}

    class _HttpErrorClient:
        def __enter__(self) -> _HttpErrorClient:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            return _HttpErrorResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: _HttpErrorClient())

    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is False
    assert provider.error == "HTTP 503"


def test_validate_config_logs_failures(monkeypatch) -> None:
    wizard = SetupWizard(non_interactive=True)
    captured: list[tuple[str, str | None]] = []

    monkeypatch.setattr(
        "abersetz.setup.validate_engines",
        lambda config, include_defaults=True: [
            type(
                "Result",
                (),
                {"selector": "tr/google", "success": False, "latency": 0.1, "error": "boom"},
            )
        ],
    )

    def fake_warning(message: str, selector: str, error: str) -> None:
        captured.append((selector, error))

    monkeypatch.setattr("abersetz.setup.logger.warning", fake_warning)

    wizard._validate_config(AbersetzConfig())

    assert captured == [("tr/google", "boom")]


def test_validate_config_returns_immediately_when_no_results(monkeypatch) -> None:
    wizard = SetupWizard(non_interactive=True)

    monkeypatch.setattr("abersetz.setup.validate_engines", lambda config, include_defaults=True: [])

    def fail_print(*args: Any, **kwargs: Any) -> None:  # pragma: no cover - guard
        raise AssertionError("console.print should not be called when no results")

    monkeypatch.setattr("abersetz.setup.console.print", fail_print)

    wizard._validate_config(AbersetzConfig())

    assert wizard.validation_results == []


def test_test_endpoints_handles_non_api_providers(monkeypatch) -> None:
    wizard = SetupWizard(non_interactive=True)
    wizard.discovered_providers = [
        DiscoveredProvider(
            name="google",
            api_key_env="GOOGLE_API_KEY",
            is_available=False,
        )
    ]

    wizard._test_endpoints()

    provider = wizard.discovered_providers[0]
    assert provider.is_available is True
    assert provider.model_count == 1


def test_test_endpoints_invokes_single_endpoint_for_api_providers(monkeypatch) -> None:
    calls: list[DiscoveredProvider] = []

    def _capture_single_endpoint(self: SetupWizard, provider: DiscoveredProvider) -> None:
        calls.append(provider)
        provider.is_available = True

    wizard = SetupWizard(non_interactive=True)
    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        is_available=False,
    )
    wizard.discovered_providers = [provider]

    monkeypatch.setattr(SetupWizard, "_test_single_endpoint", _capture_single_endpoint)

    wizard._test_endpoints()

    assert calls == [provider]
    assert provider.is_available is True


def test_test_single_endpoint_uses_anthropic_headers(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class _Client:
        def __enter__(self) -> _Client:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            calls.append({"url": url, "headers": headers})

            class _Resp:
                status_code = 200

                @staticmethod
                def json() -> dict[str, list[int]]:
                    return {"data": [1, 2]}

            return _Resp()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-token")
    monkeypatch.setattr(httpx, "Client", lambda *_, **__: _Client())

    provider = DiscoveredProvider(
        name="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com/v1",
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is True
    assert provider.model_count == 2
    assert calls and calls[0]["headers"]["anthropic-version"] == "2023-06-01"


def test_test_single_endpoint_defaults_model_count_for_unknown_payload(monkeypatch) -> None:
    class _OddResponse:
        status_code = 200

        @staticmethod
        def json() -> str:
            return "unexpected"

    class _Client:
        def __enter__(self) -> _Client:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            return _OddResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(httpx, "Client", lambda *_, **__: _Client())

    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is True
    assert provider.model_count == 1


def test_test_single_endpoint_logs_failure_when_verbose(monkeypatch) -> None:
    from loguru import logger

    class _FailureResponse:
        status_code = 500

        @staticmethod
        def json() -> dict[str, str]:  # pragma: no cover - not called
            return {}

    class _Client:
        def __enter__(self) -> _Client:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            return _FailureResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(httpx, "Client", lambda *_, **__: _Client())

    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )

    captured: list[str] = []
    token = logger.add(lambda message: captured.append(str(message)), level="DEBUG")
    try:
        SetupWizard(non_interactive=True, verbose=True)._test_single_endpoint(provider)
    finally:
        logger.remove(token)

    assert provider.is_available is False
    assert provider.error == "HTTP 500"
    assert any("✗ openai" in message for message in captured)


def test_test_single_endpoint_general_exception(monkeypatch) -> None:
    class _Client:
        def __enter__(self) -> _Client:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            raise RuntimeError("broken")

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(httpx, "Client", lambda *_, **__: _Client())

    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is False
    assert provider.error == "broken"


def test_generate_config_returns_none_when_empty() -> None:
    wizard = SetupWizard(non_interactive=True)
    wizard.discovered_providers = []

    assert wizard._generate_config() is None


def test_setup_wizard_run_interactive_success(monkeypatch) -> None:
    import io

    from rich.console import Console

    output = io.StringIO()
    monkeypatch.setattr("abersetz.setup.console", Console(file=output, force_terminal=True))

    updates: list[int] = []

    class _Progress:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            return None

        def __enter__(self) -> _Progress:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def add_task(self, description: str, total: int) -> str:
            assert "Validating" in description
            return "task"

        def update(self, task: str, advance: int) -> None:
            updates.append(advance)

    monkeypatch.setattr("abersetz.setup.Progress", _Progress)

    def fake_discover(self: SetupWizard) -> None:
        self.discovered_providers = [
            DiscoveredProvider(
                name="google",
                api_key_env="GOOGLE_API_KEY",
                base_url=None,
                is_available=True,
                engine_names=["tr/google"],
                pricing_hint="Community",
            )
        ]

    monkeypatch.setattr(SetupWizard, "_discover_providers", fake_discover)
    monkeypatch.setattr("abersetz.setup.save_config", lambda cfg: None)
    monkeypatch.setattr(SetupWizard, "_validate_config", lambda self, cfg: None)

    def fake_generate(self: SetupWizard) -> AbersetzConfig:
        config = AbersetzConfig()
        config.defaults.engine = "tr/google"
        return config

    monkeypatch.setattr(SetupWizard, "_generate_config", fake_generate)

    wizard = SetupWizard(non_interactive=False)
    assert wizard.run() is True

    text = output.getvalue()
    assert "Abersetz Configuration Setup" in text
    assert "Configuration saved" in text
    assert sum(updates) == 1


def test_setup_wizard_run_interactive_no_config(monkeypatch) -> None:
    import io

    from rich.console import Console

    output = io.StringIO()
    monkeypatch.setattr("abersetz.setup.console", Console(file=output, force_terminal=True))
    monkeypatch.setattr("abersetz.setup.Progress", lambda *args, **kwargs: _StubProgress())

    def fake_discover(self: SetupWizard) -> None:
        self.discovered_providers = []

    monkeypatch.setattr(SetupWizard, "_discover_providers", fake_discover)
    monkeypatch.setattr(SetupWizard, "_generate_config", lambda self: None)
    monkeypatch.setattr(SetupWizard, "_test_endpoints", lambda self: None)
    monkeypatch.setattr(SetupWizard, "_display_results", lambda self: None)

    wizard = SetupWizard(non_interactive=False)
    assert wizard.run() is False

    import re

    text = output.getvalue()
    clean_text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    assert "No API keys found" in clean_text
    assert "export OPENAI_API_KEY" in clean_text


def test_validate_config_renders_table(monkeypatch) -> None:
    import io

    from rich.console import Console

    output = io.StringIO()
    monkeypatch.setattr("abersetz.setup.console", Console(file=output, force_terminal=True))

    wizard = SetupWizard(non_interactive=False)

    from abersetz.validation import ValidationResult

    results = [
        ValidationResult(
            selector="tr/google", success=True, translation="hola", error=None, latency=0.1
        ),
        ValidationResult(
            selector="dt/deepl", success=False, translation="", error="boom", latency=0.2
        ),
    ]

    monkeypatch.setattr(
        "abersetz.setup.validate_engines", lambda config, include_defaults=True: results
    )

    wizard._validate_config(AbersetzConfig())

    text = output.getvalue()
    assert "Validating configured engines" in text
    assert "dt/deepl" in text


def test_discover_providers_verbose_logs(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setenv("GOOGLE_API_KEY", "token")
    monkeypatch.setattr("abersetz.setup.logger.debug", lambda message: calls.append(message))

    wizard = SetupWizard(non_interactive=True, verbose=True)
    wizard._discover_providers()

    assert any("GOOGLE_API_KEY" in message for message in calls)


def test_test_single_endpoint_connect_error(monkeypatch) -> None:
    class _Client:
        def __enter__(self) -> _Client:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            raise httpx.ConnectError("boom", request=None)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(httpx, "Client", lambda *_, **__: _Client())

    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is False
    assert provider.error == "Connection failed"


def test_test_single_endpoint_handles_json_errors(monkeypatch) -> None:
    class _Response:
        status_code = 200

        @staticmethod
        def json() -> dict[str, Any]:
            raise ValueError("bad json")

    class _Client:
        def __enter__(self) -> _Client:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str, headers: dict[str, str]):
            return _Response()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(httpx, "Client", lambda *_, **__: _Client())

    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is True
    assert provider.model_count == 1


def test_test_single_endpoint_no_base_url() -> None:
    provider = DiscoveredProvider(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url=None,
    )

    SetupWizard(non_interactive=True)._test_single_endpoint(provider)

    assert provider.is_available is False
    assert provider.model_count == 0


def test_display_results_no_providers(monkeypatch) -> None:
    import io

    from rich.console import Console

    output = io.StringIO()
    monkeypatch.setattr("abersetz.setup.console", Console(file=output, force_terminal=True))

    wizard = SetupWizard(non_interactive=False)
    wizard.discovered_providers = []

    wizard._display_results()

    assert output.getvalue() == ""


def test_select_default_engine_prefers_deepl(monkeypatch: pytest.MonkeyPatch) -> None:
    engines = {
        "deep-translator": EngineConfig(name="deep-translator", chunk_size=800, options={}),
        "translators": EngineConfig(name="translators", chunk_size=800, options={}),
    }
    providers = [
        DiscoveredProvider(
            name="deepl", api_key_env="DEEPL_API_KEY", base_url="", is_available=True
        ),
    ]

    assert _select_default_engine(engines, providers) == "deep-translator/deepl"


def test_select_default_engine_prefers_translators_then_hysf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engines = {
        "translators": EngineConfig(name="translators", chunk_size=800, options={}),
        "hysf": EngineConfig(name="hysf", chunk_size=2400, options={}),
        "ullm": EngineConfig(name="ullm", chunk_size=2400, options={}),
    }
    providers = [
        DiscoveredProvider(name="bing", api_key_env="BING_KEY", base_url="", is_available=True)
    ]

    assert _select_default_engine(engines, providers) == "tr/google"


def test_select_default_engine_prefers_ullm_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    engines = {
        "ullm": EngineConfig(name="ullm", chunk_size=2400, options={}),
        "custom": EngineConfig(name="custom", chunk_size=100, options={}),
    }
    providers = [
        DiscoveredProvider(
            name="openai", api_key_env="OPENAI_API_KEY", base_url="", is_available=True
        )
    ]

    assert _select_default_engine(engines, providers) == "ullm/default"


def test_select_default_engine_falls_back_to_first_engine() -> None:
    engines = {
        "custom": EngineConfig(name="custom", chunk_size=123, options={}),
        "second": EngineConfig(name="second", chunk_size=456, options={}),
    }
    providers: list[DiscoveredProvider] = []

    assert _select_default_engine(engines, providers) == "custom"


def test_select_default_engine_returns_none_when_empty() -> None:
    providers: Sequence[DiscoveredProvider] = []

    assert _select_default_engine({}, providers) is None


def test_generate_config_uses_fallbacks(monkeypatch) -> None:
    monkeypatch.setattr(
        "abersetz.setup.collect_translator_providers", lambda include_paid=False: []
    )
    monkeypatch.setattr(
        "abersetz.setup.collect_deep_translator_providers", lambda include_paid=False: []
    )
    monkeypatch.setattr("abersetz.setup.FREE_TRANSLATOR_PROVIDERS", ["google"])
    monkeypatch.setattr("abersetz.setup.DEEP_TRANSLATOR_FREE_PROVIDERS", ["google"])

    wizard = SetupWizard(non_interactive=True)
    wizard.discovered_providers = [
        DiscoveredProvider(
            name="openai",
            api_key_env="OPENAI_API_KEY",
            base_url="https://api.openai.com/v1",
            is_available=True,
        )
    ]

    config = wizard._generate_config()

    assert config is not None
    assert "translators" in config.engines
    assert "deep-translator" in config.engines
    ullm_engine = config.engines["ullm"]
    assert ullm_engine.credential is not None
    assert ullm_engine.credential.name == "openai"
    assert config.defaults.engine == "tr/google"


def test_setup_command_exits_on_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "abersetz.setup.SetupWizard",
        lambda *args, **kwargs: type("W", (), {"run": staticmethod(lambda: False)})(),
    )

    with pytest.raises(SystemExit):
        setup_command(non_interactive=True)


def test_setup_command_succeeds(monkeypatch) -> None:
    called: list[bool] = []

    class _Wizard:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            return None

        def run(self) -> bool:
            called.append(True)
            return True

    monkeypatch.setattr("abersetz.setup.SetupWizard", _Wizard)

    setup_command(non_interactive=True)

    assert called == [True]
