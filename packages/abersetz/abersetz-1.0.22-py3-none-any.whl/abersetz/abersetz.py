"""Legacy shim exporting the primary pipeline API."""
# this_file: src/abersetz/abersetz.py

from __future__ import annotations

from .pipeline import PipelineError, TranslationResult, TranslatorOptions, translate_path

__all__ = [
    "PipelineError",
    "TranslationResult",
    "TranslatorOptions",
    "translate_path",
]
