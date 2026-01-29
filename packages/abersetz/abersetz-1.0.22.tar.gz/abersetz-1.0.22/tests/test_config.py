"""Tests for configuration handling."""
# this_file: tests/test_config.py

from __future__ import annotations

from pathlib import Path

import pytest

import abersetz.config as config_module

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore


def test_load_config_yields_defaults(tmp_path: Path) -> None:
    cfg = config_module.load_config()
    assert cfg.defaults.engine == "tr/google"
    assert cfg.defaults.to_lang == "en"
    assert cfg.engines["hysf"].options["model"] == "tencent/Hunyuan-MT-7B"
    assert cfg.credentials["siliconflow"].env == "SILICONFLOW_API_KEY"
    assert "providers" in cfg.engines["translators"].options
    assert "providers" in cfg.engines["deep-translator"].options


def test_save_config_persists_changes(tmp_path: Path) -> None:
    cfg = config_module.load_config()
    cfg.defaults.engine = "deep-translator/google"
    config_module.save_config(cfg)
    stored = tomllib.loads(Path(config_module.config_path()).read_text(encoding="utf-8"))
    assert stored["defaults"]["engine"] == "dt/google"
    assert cfg.defaults.engine == "dt/google"


def test_resolve_credential_prefers_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = config_module.load_config()
    monkeypatch.setenv("SILICONFLOW_API_KEY", "from_env")
    resolved = config_module.resolve_credential(cfg, cfg.engines["hysf"].credential)
    assert resolved == "from_env"
    monkeypatch.delenv("SILICONFLOW_API_KEY")
    resolved_direct = config_module.resolve_credential(
        cfg,
        {"value": "direct"},
    )
    assert resolved_direct == "direct"


def test_load_config_handles_malformed_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that malformed TOML config files are handled gracefully."""
    # Set custom config dir to tmp_path
    monkeypatch.setenv("ABERSETZ_CONFIG_DIR", str(tmp_path))

    # Write malformed TOML to config file
    config_file = tmp_path / "config.toml"
    config_file.write_text('[defaults\nengine = "invalid"', encoding="utf-8")

    # Should return defaults with a warning instead of crashing
    cfg = config_module.load_config()
    assert cfg.defaults.engine == "tr/google"

    # Config should be reset to defaults
    assert config_file.exists()
    stored = tomllib.loads(config_file.read_text(encoding="utf-8"))
    assert stored["defaults"]["engine"] == "tr/google"


def test_load_config_handles_permission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that permission errors are handled gracefully."""
    # Set custom config dir to tmp_path
    monkeypatch.setenv("ABERSETZ_CONFIG_DIR", str(tmp_path))

    # Create config file and make it unreadable (skip on Windows)
    import platform

    if platform.system() != "Windows":
        config_file = tmp_path / "config.toml"
        config_file.write_text("[defaults]", encoding="utf-8")
        config_file.chmod(0o000)

        # Should return defaults without crashing
        cfg = config_module.load_config()
        assert cfg.defaults.engine == "tr/google"

        # Restore permissions for cleanup
        config_file.chmod(0o644)


def test_defaults_normalize_legacy_selector() -> None:
    defaults = config_module.Defaults(engine="translators/google")
    assert defaults.engine == "tr/google"


def test_defaults_from_dict_normalizes_selector() -> None:
    defaults = config_module.Defaults.from_dict({"engine": "deep-translator/deepl"})
    assert defaults.engine == "dt/deepl"


def test_defaults_from_dict_when_none_returns_defaults() -> None:
    defaults = config_module.Defaults.from_dict(None)

    assert defaults.engine == "tr/google"
    assert defaults.from_lang == "auto"
    assert defaults.to_lang == "en"
    assert defaults.chunk_size == 1200
    assert defaults.html_chunk_size == 1800


def test_engine_config_from_dict_when_none_returns_empty_block() -> None:
    cfg = config_module.EngineConfig.from_dict("translators", None)

    assert cfg.name == "translators"
    assert cfg.chunk_size is None
    assert cfg.html_chunk_size is None
    assert cfg.credential is None
    assert cfg.options == {}


def test_engine_config_to_dict_includes_optional_fields() -> None:
    cred = config_module.Credential(name="api", env="API", value="secret")
    cfg = config_module.EngineConfig(
        name="translators",
        chunk_size=900,
        html_chunk_size=1200,
        credential=cred,
        options={"providers": ["google"]},
    )

    payload = cfg.to_dict()

    assert payload["chunk_size"] == 900
    assert payload["html_chunk_size"] == 1200
    assert payload["credential"] == cred.to_dict()
    assert payload["options"] == {"providers": ["google"]}


def test_credential_to_dict_includes_optional_fields() -> None:
    cred = config_module.Credential(name="api", env="API_KEY", value="secret")

    payload = cred.to_dict()

    assert payload == {"name": "api", "env": "API_KEY", "value": "secret"}


def test_credential_from_any_rejects_unsupported_payload() -> None:
    with pytest.raises(TypeError):
        config_module.Credential.from_any(["invalid"])  # type: ignore[arg-type]


def test_credential_from_any_handles_mapping_payload() -> None:
    cred = config_module.Credential.from_any({"name": "api", "value": "direct"})

    assert isinstance(cred, config_module.Credential)
    assert cred.name == "api"
    assert cred.env is None
    assert cred.value == "direct"


def test_config_dir_when_env_missing_then_uses_platformdirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = tmp_path / "platform"
    monkeypatch.delenv("ABERSETZ_CONFIG_DIR", raising=False)
    monkeypatch.setattr(
        config_module,
        "user_config_dir",
        lambda appname, appauthor: str(sentinel),
    )
    assert config_module.config_dir() == sentinel


def test_resolve_credential_when_env_missing_then_logs_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from loguru import logger

    monkeypatch.delenv("MISSING_KEY", raising=False)
    cfg = config_module.AbersetzConfig()
    messages: list[str] = []
    token = logger.add(lambda message: messages.append(str(message)), level="DEBUG")
    try:
        resolved = config_module.resolve_credential(
            cfg,
            config_module.Credential(name="missing", env="MISSING_KEY"),
        )
    finally:
        logger.remove(token)
    assert resolved is None
    assert any("Environment variable 'MISSING_KEY' not set" in line for line in messages)
    assert any("Please set the 'MISSING_KEY'" in line for line in messages)


def test_resolve_credential_recurses_into_stored_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from loguru import logger

    monkeypatch.delenv("CHAINED_KEY", raising=False)
    cfg = config_module.AbersetzConfig(
        credentials={
            "alias": config_module.Credential(
                name="alias",
                env="CHAINED_KEY",
                value="stored-secret",
            )
        }
    )

    messages: list[str] = []
    token = logger.add(lambda message: messages.append(str(message)), level="DEBUG")
    try:
        resolved = config_module.resolve_credential(cfg, "alias")
    finally:
        logger.remove(token)

    assert resolved == "stored-secret"
    assert any("Environment variable 'CHAINED_KEY' not set" in line for line in messages)


def test_resolve_credential_with_recursive_name_logs_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from loguru import logger

    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)
    credential = config_module.Credential(
        name="siliconflow",
        env="SILICONFLOW_API_KEY",
    )
    cfg = config_module.AbersetzConfig(credentials={"siliconflow": credential})

    info_messages: list[str] = []
    token = logger.add(lambda message: info_messages.append(str(message)), level="INFO")
    try:
        resolved = config_module.resolve_credential(cfg, credential)
    finally:
        logger.remove(token)

    assert resolved is None
    assert sum("Please set the 'SILICONFLOW_API_KEY'" in line for line in info_messages) == 1


def test_resolve_credential_returns_none_for_null_reference() -> None:
    cfg = config_module.AbersetzConfig()

    assert config_module.resolve_credential(cfg, None) is None


def test_resolve_credential_reuses_stored_alias_object() -> None:
    credential = config_module.Credential(name="alias", value="stored")
    cfg = config_module.AbersetzConfig(credentials={"alias": credential})

    assert config_module.resolve_credential(cfg, credential) == "stored"
