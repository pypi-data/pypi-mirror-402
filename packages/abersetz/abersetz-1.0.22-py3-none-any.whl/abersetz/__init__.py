"""Public package surface for abersetz."""
# this_file: src/abersetz/__init__.py

from __future__ import annotations

from importlib import metadata as _metadata
from typing import TYPE_CHECKING, Any

# Only import types for static analysis
if TYPE_CHECKING:
    from .pipeline import PipelineError, TranslationResult, TranslatorOptions, translate_path

# Lazy loading implementation
_LAZY_IMPORTS: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy load heavy modules only when accessed."""
    if name in _LAZY_IMPORTS:
        return _LAZY_IMPORTS[name]

    # Lazy load pipeline module components
    if name in ("PipelineError", "TranslationResult", "TranslatorOptions", "translate_path"):
        from . import pipeline

        _LAZY_IMPORTS["PipelineError"] = pipeline.PipelineError
        _LAZY_IMPORTS["TranslationResult"] = pipeline.TranslationResult
        _LAZY_IMPORTS["TranslatorOptions"] = pipeline.TranslatorOptions
        _LAZY_IMPORTS["translate_path"] = pipeline.translate_path
        return _LAZY_IMPORTS[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Version handling - lightweight
try:
    __version__ = _metadata.version("abersetz")
except _metadata.PackageNotFoundError:  # pragma: no cover - fallback for local dev
    from .__about__ import __version__  # type: ignore

__all__ = [
    "PipelineError",
    "TranslationResult",
    "TranslatorOptions",
    "__version__",
    "translate_path",
]
