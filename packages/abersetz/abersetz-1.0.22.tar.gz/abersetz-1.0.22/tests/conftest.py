"""Test configuration for abersetz."""
# this_file: tests/conftest.py

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def _temp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate persisted config for each test run."""
    config_root = tmp_path / "config"
    monkeypatch.setenv("ABERSETZ_CONFIG_DIR", str(config_root))
    return config_root
