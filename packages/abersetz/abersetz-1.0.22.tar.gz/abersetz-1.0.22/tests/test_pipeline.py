"""Integration tests for the translation pipeline."""
# this_file: tests/test_pipeline.py

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from abersetz.chunking import TextFormat
from abersetz.config import AbersetzConfig
from abersetz.engines import EngineResult
from abersetz.pipeline import PipelineError, TranslatorOptions, translate_path


class DummyEngine:
    """Minimal engine used for pipeline tests."""

    def __init__(self) -> None:
        self.name = "dummy"
        self.chunk_size: int = 5
        self.html_chunk_size: int | None = None
        self.chunks: list[str] = []

    def chunk_size_for(self, _fmt) -> int:
        return self.chunk_size

    def translate(self, request) -> EngineResult:
        self.chunks.append(request.text)
        voc = dict(request.voc)
        voc[f"chunk_{len(self.chunks)}"] = request.text.upper()
        return EngineResult(text=request.text.upper(), voc=voc)


def test_translate_path_processes_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src_dir = tmp_path / "docs"
    src_dir.mkdir()
    source = src_dir / "sample.txt"
    source.write_text("hello world", encoding="utf-8")

    dummy = DummyEngine()
    monkeypatch.setattr("abersetz.pipeline.create_engine", lambda *args, **kwargs: dummy)

    options = TranslatorOptions(output_dir=tmp_path / "out", save_voc=True, chunk_size=4)
    results = translate_path(src_dir, options)

    assert len(results) == 1, "Expected a single translation result for the directory"
    output_file = tmp_path / "out" / "sample.txt"
    assert output_file.read_text(encoding="utf-8") == "HELLO WORLD"
    vocab_file = output_file.with_suffix(output_file.suffix + ".voc.json")
    saved_vocab = vocab_file.read_text(encoding="utf-8")
    assert "chunk_1" in saved_vocab
    assert dummy.chunks  # ensure engine invoked


def test_translate_path_accepts_string_source_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src_dir = tmp_path / "docs"
    src_dir.mkdir()
    source = src_dir / "sample.txt"
    source.write_text("hello world", encoding="utf-8")

    dummy = DummyEngine()
    monkeypatch.setattr("abersetz.pipeline.create_engine", lambda *args, **kwargs: dummy)

    options = TranslatorOptions(output_dir=tmp_path / "out")
    results = translate_path(str(src_dir), options)

    assert len(results) == 1, "Expected a single translation result for the directory"
    destination = tmp_path / "out" / "sample.txt"
    assert destination.exists(), "Destination file must be created in output directory"
    assert destination.read_text(encoding="utf-8") == "HELLO WORLD", (
        "Engine should uppercase text for verification"
    )
    assert results[0].destination == destination, (
        "TranslationResult destination should match written file"
    )


def test_translate_path_normalizes_engine_selector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src_file = tmp_path / "sample.txt"
    src_file.write_text("hello", encoding="utf-8")

    dummy = DummyEngine()
    captured: dict[str, str] = {}

    def fake_create_engine(selector: str, config, client=None):
        captured["selector"] = selector
        return dummy

    monkeypatch.setattr("abersetz.pipeline.create_engine", fake_create_engine)

    options = TranslatorOptions(
        engine="translators/google",
        output_dir=tmp_path / "out",
    )

    translate_path(src_file, options)

    assert captured["selector"] == "tr/google"


def test_translate_path_requires_matches(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(PipelineError):
        translate_path(empty, TranslatorOptions(include=("*.doesnotexist",)))


def test_translate_path_uses_engine_chunk_size_when_defaults_falsy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src_dir = tmp_path / "docs"
    src_dir.mkdir()
    source = src_dir / "sample.txt"
    source.write_text("hello world", encoding="utf-8")

    class ChunkyEngine(DummyEngine):
        def __init__(self) -> None:
            super().__init__()
            self.chunk_size = 3
            self.calls: list[TextFormat] = []

        def chunk_size_for(self, fmt) -> int:
            self.calls.append(fmt)
            return self.chunk_size

    engine = ChunkyEngine()

    def fake_create_engine(selector, config, client=None):
        return engine

    monkeypatch.setattr("abersetz.pipeline.create_engine", fake_create_engine)

    config = AbersetzConfig()
    config.defaults.chunk_size = 0
    config.defaults.html_chunk_size = 0

    options = TranslatorOptions(output_dir=tmp_path / "out")
    results = translate_path(src_dir, options, config=config)

    assert engine.calls, "Engine chunk_size_for should be invoked when defaults are falsy"
    assert results[0].chunk_size == engine.chunk_size, (
        "Pipeline must honour engine-provided chunk size"
    )


def test_translate_path_uses_dummy_chunk_size_when_defaults_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class TrackingDummy(DummyEngine):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[TextFormat] = []
            self.chunk_size = 7

        def chunk_size_for(self, fmt: TextFormat) -> int:
            self.calls.append(fmt)
            return super().chunk_size_for(fmt)

    src_dir = tmp_path / "docs"
    src_dir.mkdir()
    source = src_dir / "sample.txt"
    source.write_text("hello world", encoding="utf-8")

    engine = TrackingDummy()
    monkeypatch.setattr("abersetz.pipeline.create_engine", lambda *args, **kwargs: engine)

    config = AbersetzConfig()
    config.defaults.chunk_size = 0
    config.defaults.html_chunk_size = 0

    options = TranslatorOptions(output_dir=tmp_path / "out")
    results = translate_path(src_dir, options, config=config)

    assert engine.calls == [TextFormat.PLAIN], (
        "Engine chunk_size_for should be consulted for plain text"
    )
    assert results[0].chunk_size == engine.chunk_size, (
        "Pipeline must use engine-provided chunk size"
    )


def test_translate_path_html_uses_engine_chunk_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src_dir = tmp_path / "docs"
    src_dir.mkdir()
    source = src_dir / "sample.html"
    source.write_text("<p>Hello world</p>", encoding="utf-8")

    class HtmlEngine(DummyEngine):
        def __init__(self) -> None:
            super().__init__()
            self.chunk_size = 2
            self.html_chunk_size = 9
            self.calls: list[TextFormat] = []

        def chunk_size_for(self, fmt: TextFormat) -> int:
            self.calls.append(fmt)
            if fmt is TextFormat.HTML:
                assert self.html_chunk_size is not None
                return self.html_chunk_size
            return self.chunk_size

    engine = HtmlEngine()
    monkeypatch.setattr("abersetz.pipeline.create_engine", lambda *args, **kwargs: engine)

    config = AbersetzConfig()
    config.defaults.chunk_size = 0
    config.defaults.html_chunk_size = 0

    options = TranslatorOptions(output_dir=tmp_path / "out")
    results = translate_path(src_dir, options, config=config)

    assert engine.calls and engine.calls[0] is TextFormat.HTML, (
        "HTML chunk size path must invoke engine hint first"
    )
    assert results[0].chunk_size == engine.html_chunk_size, (
        "Pipeline should honour engine-provided HTML chunk size"
    )
    assert results[0].format is TextFormat.HTML, (
        "Result format should remain HTML after translation"
    )


def test_translate_path_with_html_engine_handles_mixed_formats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src_dir = tmp_path / "mixed"
    src_dir.mkdir()
    text_file = src_dir / "note.txt"
    text_file.write_text("hello world", encoding="utf-8")
    html_file = src_dir / "page.html"
    html_file.write_text("<p>Hello world</p>", encoding="utf-8")

    class TrackingHtmlEngine(DummyEngine):
        def __init__(self) -> None:
            super().__init__()
            self.chunk_size = 3
            self.html_chunk_size = 9
            self.calls: list[TextFormat] = []

        def chunk_size_for(self, fmt: TextFormat) -> int:
            self.calls.append(fmt)
            if fmt is TextFormat.HTML:
                assert self.html_chunk_size is not None
                return self.html_chunk_size
            return self.chunk_size

    engine = TrackingHtmlEngine()
    monkeypatch.setattr("abersetz.pipeline.create_engine", lambda *args, **kwargs: engine)

    config = AbersetzConfig()
    config.defaults.chunk_size = 0
    config.defaults.html_chunk_size = 0

    options = TranslatorOptions(output_dir=tmp_path / "out", recurse=False)
    results = translate_path(src_dir, options, config=config)

    formats_to_sizes = {result.format: result.chunk_size for result in results}

    assert TextFormat.HTML in engine.calls and TextFormat.PLAIN in engine.calls, (
        "Engine must see both HTML and plain formats"
    )
    assert formats_to_sizes[TextFormat.HTML] == engine.html_chunk_size
    assert formats_to_sizes[TextFormat.PLAIN] == engine.chunk_size


def test_translate_path_handles_mixed_formats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src_dir = tmp_path / "mixed"
    src_dir.mkdir()
    text_file = src_dir / "note.txt"
    text_file.write_text("hello world", encoding="utf-8")
    html_file = src_dir / "page.html"
    html_file.write_text("<p>Hello <strong>world</strong></p>", encoding="utf-8")

    dummy = DummyEngine()
    monkeypatch.setattr("abersetz.pipeline.create_engine", lambda *args, **kwargs: dummy)

    output_dir = tmp_path / "out"
    options = TranslatorOptions(
        engine="tr/google",
        output_dir=output_dir,
        recurse=False,
        save_voc=True,
    )

    results = translate_path(src_dir, options)

    assert {item.source.name for item in results} == {"note.txt", "page.html"}
    for item in results:
        assert item.destination.parent == output_dir
        assert item.destination.exists()
        assert item.engine == "tr/google"
        assert item.chunks >= 1
        assert item.voc
        assert item.chunk_size > 0

    # Ensure HTML detection preserved format metadata
    formats = {item.source.suffix: item.format for item in results}
    assert formats[".txt"] is TextFormat.PLAIN
    assert formats[".html"] is TextFormat.HTML

    # Dummy engine should have been called for both files
    assert len(dummy.chunks) == 2


@pytest.mark.skipif(sys.platform.startswith("win"), reason="chmod semantics differ on Windows")
def test_translate_path_errors_on_unreadable_file(tmp_path: Path) -> None:
    protected = tmp_path / "private.txt"
    protected.write_text("secret", encoding="utf-8")
    protected.chmod(0o000)

    try:
        with pytest.raises(PipelineError) as excinfo:
            translate_path(protected, TranslatorOptions())
    finally:
        protected.chmod(0o600)

    message = str(excinfo.value)
    assert "Cannot read" in message
    assert "private.txt" in message


def test_translate_path_write_over_updates_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "note.txt"
    source.write_text("hello", encoding="utf-8")

    dummy = DummyEngine()
    monkeypatch.setattr("abersetz.pipeline.create_engine", lambda *args, **kwargs: dummy)

    options = TranslatorOptions(write_over=True, save_voc=True)
    results = translate_path(source, options)

    assert results
    assert results[0].destination == source
    assert source.read_text(encoding="utf-8") == "HELLO"
    vocab_path = source.with_suffix(source.suffix + ".voc.json")
    assert vocab_path.exists()
    assert "chunk_1" in vocab_path.read_text(encoding="utf-8")


def test_translate_path_dry_run_skips_io(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "note.txt"
    source.write_text("hello", encoding="utf-8")
    output_dir = tmp_path / "out"

    dummy = DummyEngine()
    monkeypatch.setattr("abersetz.pipeline.create_engine", lambda *args, **kwargs: dummy)

    options = TranslatorOptions(output_dir=output_dir, save_voc=True, dry_run=True)
    results = translate_path(source, options)

    assert results
    destination = output_dir / "note.txt"
    assert results[0].destination == destination
    assert not destination.exists()
    assert not destination.with_suffix(destination.suffix + ".voc.json").exists()


def test_translate_path_warns_on_large_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from loguru import logger

    source = tmp_path / "big.txt"
    source.write_text("data", encoding="utf-8")

    dummy = DummyEngine()
    monkeypatch.setattr("abersetz.pipeline.create_engine", lambda *_, **__: dummy)

    real_stat = Path.stat
    fake_big_stat = os.stat_result((0o100644, 0, 0, 1, 0, 0, 11 * 1024 * 1024, 0, 0, 0))

    def fake_stat(self: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        if self == source:
            return fake_big_stat
        return real_stat(self, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(Path, "stat", fake_stat)

    warnings: list[str] = []
    token = logger.add(lambda message: warnings.append(str(message)), level="WARNING")
    try:
        results = translate_path(source, TranslatorOptions(output_dir=tmp_path / "out"))
    finally:
        logger.remove(token)

    assert results
    assert any("Large file detected" in entry for entry in warnings)
