"""Configuration helpers for abersetz."""
# this_file: src/abersetz/config.py

from __future__ import annotations

import copy
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

from .engine_catalog import (
    DEEP_TRANSLATOR_FREE_PROVIDERS,
    FREE_TRANSLATOR_PROVIDERS,
    HYSF_DEFAULT_MODEL,
    HYSF_DEFAULT_TEMPERATURE,
    normalize_selector,
)

try:  # Python >= 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for Python 3.10
    import tomli as tomllib  # type: ignore

import tomli_w

CONFIG_FILENAME = "config.toml"


@dataclass(slots=True)
class Defaults:
    """Runtime defaults for translation."""

    engine: str = "tr/google"
    from_lang: str = "auto"
    to_lang: str = "en"
    chunk_size: int = 1200
    html_chunk_size: int = 1800

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: D401 - dataclass override
        if name == "engine" and isinstance(value, str):
            value = normalize_selector(value) or value.strip()
        object.__setattr__(self, name, value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "from_lang": self.from_lang,
            "to_lang": self.to_lang,
            "chunk_size": self.chunk_size,
            "html_chunk_size": self.html_chunk_size,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any] | None) -> Defaults:
        if raw is None:
            return cls()
        defaults = cls()
        return cls(
            engine=str(raw.get("engine", defaults.engine)),
            from_lang=str(raw.get("from_lang", defaults.from_lang)),
            to_lang=str(raw.get("to_lang", defaults.to_lang)),
            chunk_size=int(raw.get("chunk_size", defaults.chunk_size)),
            html_chunk_size=int(raw.get("html_chunk_size", defaults.html_chunk_size)),
        )


@dataclass(slots=True)
class Credential:
    """Represents an API credential reference."""

    name: str | None = None
    env: str | None = None
    value: str | None = None

    def to_dict(self) -> dict[str, str]:
        data: dict[str, str] = {}
        if self.name:
            data["name"] = self.name
        if self.env:
            data["env"] = self.env
        if self.value:
            data["value"] = self.value
        return data

    @classmethod
    def from_any(cls, raw: CredentialLike | None) -> Credential | None:
        if raw is None:
            return None
        if isinstance(raw, Credential):
            return raw
        if isinstance(raw, str):
            return cls(name=raw)
        if isinstance(raw, Mapping):
            return cls(
                name=raw.get("name"),
                env=raw.get("env"),
                value=raw.get("value"),
            )
        raise TypeError(f"Unsupported credential payload: {type(raw)!r}")


CredentialLike = Credential | Mapping[str, Any] | str | None


@dataclass(slots=True)
class EngineConfig:
    """Engine specific configuration block."""

    name: str
    chunk_size: int | None = None
    html_chunk_size: int | None = None
    credential: Credential | None = None
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"name": self.name, "options": self.options}
        if self.chunk_size is not None:
            data["chunk_size"] = self.chunk_size
        if self.html_chunk_size is not None:
            data["html_chunk_size"] = self.html_chunk_size
        if self.credential:
            data["credential"] = self.credential.to_dict()
        return data

    @classmethod
    def from_dict(cls, name: str, raw: Mapping[str, Any] | None) -> EngineConfig:
        if raw is None:
            return cls(name=name)
        return cls(
            name=name,
            chunk_size=raw.get("chunk_size"),
            html_chunk_size=raw.get("html_chunk_size"),
            credential=Credential.from_any(raw.get("credential")),
            options=dict(raw.get("options", {})),
        )


@dataclass(slots=True)
class AbersetzConfig:
    """Aggregate configuration for the toolkit."""

    defaults: Defaults = field(default_factory=Defaults)
    credentials: dict[str, Credential] = field(default_factory=dict)
    engines: dict[str, EngineConfig] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "defaults": self.defaults.to_dict(),
            "credentials": {key: cred.to_dict() for key, cred in self.credentials.items()},
            "engines": {key: engine.to_dict() for key, engine in self.engines.items()},
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> AbersetzConfig:
        defaults = Defaults.from_dict(raw.get("defaults"))
        credentials = {
            key: Credential.from_any(value) or Credential(name=key)
            for key, value in dict(raw.get("credentials", {})).items()
        }
        engines = {
            key: EngineConfig.from_dict(key, value)
            for key, value in dict(raw.get("engines", {})).items()
        }
        return cls(defaults=defaults, credentials=credentials, engines=engines)


DEFAULT_CONFIG_DICT: dict[str, Any] = {
    "defaults": Defaults().to_dict(),
    "credentials": {
        "siliconflow": {"name": "siliconflow", "env": "SILICONFLOW_API_KEY"},
    },
    "engines": {
        "translators": {
            "name": "translators",
            "chunk_size": 800,
            "options": {
                "provider": "google",
                "providers": list(FREE_TRANSLATOR_PROVIDERS),
            },
        },
        "deep-translator": {
            "name": "deep-translator",
            "chunk_size": 800,
            "options": {
                "provider": "google",
                "providers": list(DEEP_TRANSLATOR_FREE_PROVIDERS),
            },
        },
        "hysf": {
            "name": "hysf",
            "chunk_size": 2400,
            "credential": {"name": "siliconflow"},
            "options": {
                "model": HYSF_DEFAULT_MODEL,
                "base_url": "https://api.siliconflow.com/v1",
                "temperature": HYSF_DEFAULT_TEMPERATURE,
            },
        },
        "ullm": {
            "name": "ullm",
            "chunk_size": 2400,
            "credential": {"name": "siliconflow"},
            "options": {
                "profiles": {
                    "default": {
                        "base_url": "https://api.siliconflow.com/v1",
                        "model": HYSF_DEFAULT_MODEL,
                        "temperature": HYSF_DEFAULT_TEMPERATURE,
                        "max_input_tokens": 32000,
                        "prolog": {},
                    }
                }
            },
        },
    },
}


def _default_dict() -> dict[str, Any]:
    """Return a deep copy of the default config mapping."""
    return copy.deepcopy(DEFAULT_CONFIG_DICT)


def _default_config() -> AbersetzConfig:
    """Return a fresh ``AbersetzConfig`` with defaults."""
    return AbersetzConfig.from_dict(_default_dict())


def config_dir() -> Path:
    """Return directory holding the configuration file."""
    custom = os.getenv("ABERSETZ_CONFIG_DIR")
    if custom:
        return Path(custom)
    return Path(user_config_dir(appname="abersetz", appauthor="twardoch"))


def config_path() -> Path:
    """Return absolute path to the configuration file."""
    return config_dir() / CONFIG_FILENAME


def load_config() -> AbersetzConfig:
    """Load configuration from disk, creating defaults if needed."""
    from loguru import logger

    path = config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        default = _default_config()
        save_config(default)
        return default

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, PermissionError) as e:
        logger.warning(
            f"Cannot read config file at {path}: {e}. "
            f"Using default configuration. Check file permissions."
        )
        return _default_config()

    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as error:
        logger.warning(
            f"Config file at {path} contains invalid TOML: {error}. "
            f"Resetting to defaults. Backup saved as config.toml.backup"
        )
        backup_path = path.parent / "config.toml.backup"
        try:
            backup_path.write_text(content, encoding="utf-8")
        except Exception:  # pragma: no cover - best effort backup
            pass
        default = _default_config()
        save_config(default)
        return default

    return AbersetzConfig.from_dict(data)


def save_config(config: AbersetzConfig) -> None:
    """Persist configuration to ``config.toml``."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = tomli_w.dumps(config.to_dict())
    path.write_text(content, encoding="utf-8")


def resolve_credential(
    config: AbersetzConfig,
    reference: CredentialLike,
) -> str | None:
    """Resolve a credential reference to a usable secret.

    Returns None if no credential found, logs helpful messages.
    """
    from loguru import logger

    credential = Credential.from_any(reference)
    if credential is None:
        return None
    if credential.name:
        stored = config.credentials.get(credential.name)
        if stored is not None and stored is not credential:
            return resolve_credential(config, stored)
    if credential.env:
        env_value = os.getenv(credential.env)
        if env_value:
            return env_value
        else:
            logger.debug(
                f"Environment variable '{credential.env}' not set. "
                f"Set it with: export {credential.env}=your-api-key"
            )
    if credential.value:
        return credential.value
    # Log helpful message when no credential found
    if credential.env:
        logger.info(
            f"No API key found for credential. Please set the '{credential.env}' "
            f"environment variable or add it to your config file at {config_path()}"
        )
    return None


__all__ = [
    "AbersetzConfig",
    "Credential",
    "CredentialLike",
    "Defaults",
    "EngineConfig",
    "config_dir",
    "config_path",
    "load_config",
    "resolve_credential",
    "save_config",
]
