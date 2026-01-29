"""Text detection and chunking utilities."""
# this_file: src/abersetz/chunking.py

from __future__ import annotations

import re
from collections.abc import Iterable
from enum import Enum

_HTML_PATTERN = re.compile(r"<\s*(html|body|head|div|span|p|br|!DOCTYPE)", re.IGNORECASE)


class TextFormat(Enum):
    """Minimal set of supported text formats."""

    PLAIN = "plain"
    HTML = "html"


def detect_format(text: str) -> TextFormat:
    """Detect whether ``text`` looks like HTML."""
    if _HTML_PATTERN.search(text):
        return TextFormat.HTML
    return TextFormat.PLAIN


def _fallback_chunks(text: str, max_size: int) -> list[str]:
    """Simple slicing fallback when semantic splitter is unavailable."""
    return [text[i : i + max_size] for i in range(0, len(text), max_size)]


def _semantic_chunks(text: str, max_size: int) -> Iterable[str]:
    """Prefer semantic-text-splitter when installed."""
    try:
        from semantic_text_splitter import TextSplitter
    except ImportError:  # pragma: no cover - exercised in environments without dependency
        yield from _fallback_chunks(text, max_size)
        return
    splitter = TextSplitter(max_size, trim=False)
    yield from splitter.chunks(text)


def chunk_text(text: str, max_size: int, fmt: TextFormat) -> list[str]:
    """Chunk text according to the detected format."""
    if not text:
        return []
    if fmt is TextFormat.HTML:
        return [text]
    return list(_semantic_chunks(text, max_size))


__all__ = ["TextFormat", "chunk_text", "detect_format"]
