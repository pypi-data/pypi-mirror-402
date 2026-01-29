"""Tests for chunking and detection utilities."""
# this_file: tests/test_chunking.py

from __future__ import annotations

import builtins

from abersetz.chunking import TextFormat, chunk_text, detect_format


def test_detect_format_identifies_html() -> None:
    snippet = "<html><body><p>Hello</p></body></html>"
    assert detect_format(snippet) is TextFormat.HTML


def test_chunk_text_preserves_round_trip() -> None:
    text = "\n".join(f"line {i}" for i in range(50))
    chunks = chunk_text(text, max_size=40, fmt=TextFormat.PLAIN)
    assert "".join(chunks) == text
    assert len(chunks) > 3


def test_html_chunking_returns_single_chunk() -> None:
    html = "<p>alpha</p><p>beta</p>"
    chunks = chunk_text(html, max_size=10, fmt=TextFormat.HTML)
    assert chunks == [html]


def test_chunk_text_returns_empty_for_blank_input() -> None:
    assert chunk_text("", max_size=64, fmt=TextFormat.PLAIN) == []


def test_chunk_text_fallback_runs_without_semantic_splitter(monkeypatch) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "semantic_text_splitter":
            raise ImportError("forced missing dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    math_module = __import__("math")
    assert math_module.__name__ == "math", "Fallback importer must defer to the original loader"

    text = "abcdefghij"
    chunks = chunk_text(text, max_size=4, fmt=TextFormat.PLAIN)
    assert chunks == ["abcd", "efgh", "ij"]
