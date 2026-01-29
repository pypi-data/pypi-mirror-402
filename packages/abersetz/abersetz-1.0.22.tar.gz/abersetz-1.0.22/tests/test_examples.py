"""Tests for example helper utilities."""
# this_file: tests/test_examples.py

from __future__ import annotations

import asyncio
import importlib.util
import json
import runpy
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, cast

import pytest  # type: ignore[import-not-found]

from abersetz.chunking import TextFormat
from abersetz.pipeline import TranslationResult, TranslatorOptions


class _StubResult:
    def __init__(
        self, source: str, destination: str, *, fmt: TextFormat = TextFormat.PLAIN
    ) -> None:
        self.source = Path(source)
        self.destination = Path(destination)
        self.chunks = 2
        self.format = fmt
        self.voc = {"chunk_1": "HELLO"}


class _BasicApiModule(Protocol):
    translate_path: Callable[..., object]

    def format_example_doc(self, func: Callable[..., object]) -> str: ...

    def example_simple(self) -> None: ...

    def example_batch(self) -> None: ...

    def example_dry_run(self) -> None: ...

    def example_html(self) -> None: ...

    def example_with_config(self) -> None: ...

    def example_llm_with_voc(self) -> None: ...

    def cli(self, example: str | None = None) -> None: ...


def _load_basic_api() -> _BasicApiModule:
    module_path = Path(__file__).resolve().parents[1] / "examples" / "basic_api.py"
    spec = importlib.util.spec_from_file_location("examples.basic_api", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Unable to load examples.basic_api")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(_BasicApiModule, module)


basic_api = _load_basic_api()


def _load_advanced_api():
    module_path = Path(__file__).resolve().parents[1] / "examples" / "advanced_api.py"
    spec = importlib.util.spec_from_file_location("examples.advanced_api", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Unable to load examples.advanced_api")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


advanced_api = _load_advanced_api()


def test_format_example_doc_handles_none() -> None:
    def _no_doc() -> None:  # pragma: no cover - doc intentionally missing
        return None

    _no_doc.__doc__ = None

    assert basic_api.format_example_doc(_no_doc) == "No description provided."


def test_format_example_doc_strips_whitespace() -> None:
    def _with_doc() -> None:
        """Example description with padding"""

    assert basic_api.format_example_doc(_with_doc) == "Example description with padding"


def test_example_simple_outputs_summary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: dict[str, object] = {}

    def fake_translate_path(path: str, options: TranslatorOptions) -> list[_StubResult]:
        calls["path"] = path
        calls["options"] = options
        return [_StubResult("poem_en.txt", "translations/poem_es.txt")]

    monkeypatch.setattr(basic_api, "translate_path", fake_translate_path)

    basic_api.example_simple()

    output = capsys.readouterr().out
    assert "Translated poem_en.txt -> translations/poem_es.txt" in output
    assert "Used 2 chunks in plain format" in output

    options = cast(TranslatorOptions, calls["options"])
    assert options.to_lang == "es"
    assert options.engine == "tr/google"


def test_example_batch_uses_include_filters(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: dict[str, Any] = {}

    def fake_translate_path(path: str, options: TranslatorOptions) -> list[_StubResult]:
        calls["path"] = path
        calls["options"] = options
        return [
            _StubResult("file1.txt", "translations/fr/file1.txt"),
            _StubResult("file2.md", "translations/fr/file2.md"),
        ]

    monkeypatch.setattr(basic_api, "translate_path", fake_translate_path)

    basic_api.example_batch()

    output = capsys.readouterr().out
    assert "Translated 2 files" in output

    options = cast(TranslatorOptions, calls["options"])
    assert options.include == ("*.txt", "*.md")
    assert options.xclude == ("*_fr.txt", "*_fr.md")
    assert options.output_dir == Path("translations/fr")
    assert options.engine == "dt/google"


def test_example_dry_run_lists_files(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_translate_path(path: str, options: TranslatorOptions) -> list[_StubResult]:
        return [_StubResult("test_files/sample.txt", "unused/sample.txt")]

    monkeypatch.setattr(basic_api, "translate_path", fake_translate_path)

    basic_api.example_dry_run()

    output = capsys.readouterr().out
    assert "Would translate: test_files/sample.txt" in output


def test_example_html_preserves_markup_intent(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_translate_path(path: str, options: TranslatorOptions) -> list[_StubResult]:
        return [_StubResult("website/index.html", "translations/index.html", fmt=TextFormat.HTML)]

    monkeypatch.setattr(basic_api, "translate_path", fake_translate_path)

    basic_api.example_html()

    output = capsys.readouterr().out
    assert "HTML translation complete" in output


def test_example_with_config_uses_modified_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    @dataclass
    class _Defaults:
        to_lang: str = "en"
        chunk_size: int = 500

    @dataclass
    class _Config:
        defaults: _Defaults = field(default_factory=_Defaults)
        engines: dict[str, object] = field(default_factory=dict)

    saved: dict[str, Any] = {}

    config = _Config()

    def fake_load_config() -> _Config:
        return config

    def fake_save_config(value: _Config) -> None:
        saved["config"] = value

    def fake_translate_path(
        path: str, options: TranslatorOptions | None = None, *, config: _Config
    ) -> list[_StubResult]:
        saved["call_config"] = config
        saved["options"] = options
        return [_StubResult("document.txt", "document.txt")]

    monkeypatch.setattr("abersetz.config.load_config", fake_load_config)
    monkeypatch.setattr("abersetz.config.save_config", fake_save_config)
    monkeypatch.setattr(basic_api, "translate_path", fake_translate_path)

    basic_api.example_with_config()

    assert saved["config"].defaults.to_lang == "es"
    assert saved["config"].defaults.chunk_size == 1500
    assert "custom_llm" in saved["config"].engines
    options = cast(TranslatorOptions | None, saved["options"])
    assert options is None
    assert saved["call_config"] is config


def test_example_llm_with_voc_reports_final_vocab(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_translate_path(path: str, options: TranslatorOptions) -> list[_StubResult]:
        return [_StubResult("technical_doc.md", "outputs/technical_doc.md")]

    monkeypatch.setattr(basic_api, "translate_path", fake_translate_path)

    basic_api.example_llm_with_voc()

    output = capsys.readouterr().out
    assert "Final voc" in output


def test_translation_workflow_translate_project_collects_results_and_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    collected: list[TranslationResult] = []

    def fake_translate_path(path: str, options: TranslatorOptions, *, config: object | None = None):
        if options.to_lang == "es":
            result = TranslationResult(
                source=tmp_path / "docs" / "index.md",
                destination=tmp_path / "docs_es" / "index.md",
                chunks=3,
                voc={"hello": "hola"},
                format=TextFormat.PLAIN,
            )
            collected.append(result)
            return [result]
        raise RuntimeError("boom")

    monkeypatch.setattr(advanced_api, "translate_path", fake_translate_path)

    workflow = advanced_api.TranslationWorkflow(config=advanced_api.AbersetzConfig())
    workflow.translate_project(str(tmp_path / "docs"), ["es", "fr"], engine="tr/google")

    assert [r.destination.parent.name for r in workflow.results] == ["docs_es"]
    assert workflow.errors == {"fr": "boom"}
    assert collected


def test_translation_workflow_generate_report_creates_parent_dirs(tmp_path: Path) -> None:
    workflow = advanced_api.TranslationWorkflow(config=advanced_api.AbersetzConfig())
    workflow.results = [
        TranslationResult(
            source=tmp_path / "docs" / "alpha.md",
            destination=tmp_path / "docs_es" / "alpha.md",
            chunks=2,
            voc={"one": "uno"},
            format=TextFormat.PLAIN,
        ),
        TranslationResult(
            source=tmp_path / "docs" / "beta.html",
            destination=tmp_path / "docs_es" / "beta.html",
            chunks=1,
            voc={},
            format=TextFormat.HTML,
        ),
    ]
    workflow.errors = {"fr": "boom"}

    target = tmp_path / "reports" / "daily" / "summary.json"
    report = workflow.generate_report(str(target))

    assert target.exists()
    payload = json.loads(target.read_text())
    assert payload["total_files"] == 2
    assert payload["languages"]["es"]["files"] == 2
    assert report["errors"] == {"fr": "boom"}


def test_translation_workflow_lazy_loads_config(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = object()
    calls = {"count": 0}

    def fake_load_config() -> object:
        calls["count"] += 1
        return sentinel

    monkeypatch.setattr(advanced_api, "load_config", fake_load_config)

    workflow = advanced_api.TranslationWorkflow()
    assert workflow.config is sentinel
    assert calls["count"] == 1

    provided = advanced_api.AbersetzConfig()
    workflow_with_config = advanced_api.TranslationWorkflow(config=provided)
    assert workflow_with_config.config is provided
    assert calls["count"] == 1


def test_voc_manager_translate_with_consistency_preserves_base_voc(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manager = advanced_api.vocManager()
    snapshots: list[dict[str, str]] = []
    call_count = {"value": 0}

    def fake_translate_path(path: str, options: TranslatorOptions) -> list[TranslationResult]:
        call_count["value"] += 1
        snapshots.append(dict(options.initial_voc))
        voc_payload = {"First": "One"} if call_count["value"] == 1 else {"Second": "Two"}
        return [
            TranslationResult(
                source=Path(path),
                destination=Path("build") / Path(path).name,
                chunks=1,
                voc=voc_payload,
                format=TextFormat.PLAIN,
            )
        ]

    monkeypatch.setattr(advanced_api, "translate_path", fake_translate_path)

    initial_results, initial_vocab = manager.translate_with_consistency(["doc.txt"], "es")
    assert len(initial_results) == 1
    assert initial_vocab == {"First": "One"}

    base = {"Existing": "Value"}
    followup_results, followup_vocab = manager.translate_with_consistency(
        ["doc2.txt"],
        "es",
        base_voc=base,
    )

    assert len(followup_results) == 1
    assert followup_vocab == {"Existing": "Value", "Second": "Two"}
    assert base == {"Existing": "Value"}
    assert snapshots == [{}, {"Existing": "Value"}]

    output = capsys.readouterr().out
    assert "Translating doc.txt" in output


def test_voc_manager_load_and_merge(tmp_path: Path) -> None:
    manager = advanced_api.vocManager()

    es_file = tmp_path / "en_es.json"
    fr_file = tmp_path / "es_fr.json"
    es_file.write_text(json.dumps({"hello": "hola"}), encoding="utf-8")
    fr_file.write_text(json.dumps({"hola": "bonjour"}), encoding="utf-8")

    manager.load_voc(str(es_file), "en-es")
    manager.load_voc(str(fr_file), "es-fr")

    merged = manager.merge_vocabularies("es-fr", "missing", "en-es")
    assert merged == {"hola": "bonjour", "hello": "hola"}


@pytest.mark.asyncio
async def test_parallel_translator_compare_translations_handles_failures(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    sentinel_config = object()
    monkeypatch.setattr(advanced_api, "load_config", lambda: sentinel_config)

    class _StubEngine:
        def __init__(self, name: str) -> None:
            self.name = name

        def translate(self, request: Any):
            assert request.target_lang == "es"
            if self.name == "fail":
                raise RuntimeError("kaboom")
            return type("_Result", (), {"text": f"{request.text}-{self.name}"})()

    def fake_create_engine(name: str, config: object):
        assert config is sentinel_config
        return _StubEngine(name)

    monkeypatch.setattr(advanced_api, "create_engine", fake_create_engine)

    translator = advanced_api.ParallelTranslator()
    results = await translator.compare_translations("hello", ["ok", "fail"], "es")

    output = capsys.readouterr().out
    assert "=== Translation Comparison ===" in output
    assert results["ok"] == "hello-ok"
    assert results["fail"].startswith("Error: kaboom")


def test_example_voc_consistency_writes_vocab(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manager = advanced_api.vocManager()
    expected_files = ["api_reference.md", "user_guide.md", "developer_docs.md"]

    def fake_translate_with_consistency(
        *, files: list[str], to_lang: str, base_voc: dict[str, str]
    ):
        assert files == expected_files
        assert to_lang == "es"
        assert base_voc["pipeline"] == "pipeline de procesamiento"
        return (["result"], {"API": "API"})

    monkeypatch.setattr(advanced_api, "vocManager", lambda: manager)
    monkeypatch.setattr(manager, "translate_with_consistency", fake_translate_with_consistency)
    monkeypatch.chdir(tmp_path)

    advanced_api.example_voc_consistency()

    payload = json.loads((tmp_path / "technical_voc_es.json").read_text())
    assert payload == {"API": "API"}
    output = capsys.readouterr().out
    assert "Final voc has 1 terms" in output


def test_example_parallel_comparison_invokes_async_run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    translator = advanced_api.ParallelTranslator()

    async def fake_compare(text: str, engines: list[str], to_lang: str):
        assert to_lang == "fr"
        assert engines[-1] == "hy"
        return {engine: f"{engine}-ok" for engine in engines}

    monkeypatch.setattr(advanced_api, "ParallelTranslator", lambda: translator)
    monkeypatch.setattr(translator, "compare_translations", fake_compare)

    calls: dict[str, bool] = {}

    def fake_run(coro):
        calls["ran"] = True
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    monkeypatch.setattr(advanced_api.asyncio, "run", fake_run)

    advanced_api.example_parallel_comparison()

    assert calls.get("ran") is True


def test_example_incremental_translation_processes_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    docs_dir = tmp_path / "large_docs"
    docs_dir.mkdir()
    file_a = docs_dir / "a.md"
    file_b = docs_dir / "b.md"
    file_a.write_text("alpha")
    file_b.write_text("beta")

    call_count = {"value": 0}

    def fake_translate_path(
        path: str,
        options: TranslatorOptions,
        *,
        config: object | None = None,
    ) -> list[TranslationResult]:
        call_count["value"] += 1
        if call_count["value"] == 2:
            raise RuntimeError("boom")
        return [
            TranslationResult(
                source=Path(path),
                destination=Path(path).with_suffix(".out"),
                chunks=1,
                voc={},
                format=TextFormat.PLAIN,
            )
        ]

    monkeypatch.setattr(advanced_api, "translate_path", fake_translate_path)

    advanced_api.example_incremental_translation()

    checkpoint = tmp_path / ".translation_checkpoint.json"
    assert checkpoint.exists()
    saved_paths = json.loads(checkpoint.read_text())
    relative_paths = {str(file_a.relative_to(tmp_path)), str(file_b.relative_to(tmp_path))}
    assert set(saved_paths).issubset(relative_paths)
    assert len(saved_paths) == 1
    output = capsys.readouterr().out
    assert "Failed: boom" in output


def test_example_incremental_translation_reuses_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    docs_dir = tmp_path / "large_docs"
    docs_dir.mkdir()
    done_file = docs_dir / "done.md"
    pending_file = docs_dir / "pending.md"
    done_file.write_text("done", encoding="utf-8")
    pending_file.write_text("pending", encoding="utf-8")

    checkpoint = tmp_path / ".translation_checkpoint.json"
    checkpoint.write_text(json.dumps(["large_docs/done.md"]), encoding="utf-8")

    def fake_translate_path(
        path: str,
        options: TranslatorOptions,
        *,
        config: object | None = None,
    ) -> list[TranslationResult]:
        assert path == "large_docs/pending.md"
        return [
            TranslationResult(
                source=Path(path),
                destination=Path(path).with_suffix(".out"),
                chunks=1,
                voc={},
                format=TextFormat.PLAIN,
            )
        ]

    monkeypatch.setattr(advanced_api, "translate_path", fake_translate_path)

    advanced_api.example_incremental_translation()

    saved = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert sorted(saved) == ["large_docs/done.md", "large_docs/pending.md"]
    output = capsys.readouterr().out
    assert "Already completed: 1 files" in output
    assert "Saved to" in output


def test_basic_api_cli_dispatch_runs_requested_example(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module_path = Path(__file__).resolve().parents[1] / "examples" / "basic_api.py"
    calls: dict[str, object] = {}

    def fake_translate_path(path: str, options: TranslatorOptions) -> list[_StubResult]:
        calls["path"] = path
        calls["options"] = options
        return [_StubResult("poem_en.txt", "translations/poem_es.txt")]

    monkeypatch.setattr("abersetz.translate_path", fake_translate_path)
    monkeypatch.setattr(sys, "argv", [str(module_path), "simple"])

    runpy.run_path(str(module_path), run_name="__main__")

    output = capsys.readouterr().out
    assert "Usage" not in output
    assert calls["path"] == "poem_en.txt"
    options = cast(TranslatorOptions, calls["options"])
    assert options.to_lang == "es"
    assert options.engine == "tr/google"


def test_basic_api_cli_usage_banner(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module_path = Path(__file__).resolve().parents[1] / "examples" / "basic_api.py"
    monkeypatch.setattr(sys, "argv", [str(module_path)])

    runpy.run_path(str(module_path), run_name="__main__")

    output = capsys.readouterr().out
    assert "Usage:" in output
    assert "Available examples" in output


def test_advanced_api_cli_dispatch_runs_requested_example(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module_path = Path(__file__).resolve().parents[1] / "examples" / "advanced_api.py"
    captured_paths: list[str] = []
    captured_engines: list[str] = []

    def fake_translate_path(
        path: str,
        options: TranslatorOptions,
        *,
        config: object | None = None,
    ) -> list[TranslationResult]:
        captured_paths.append(path)
        engine = options.engine
        assert engine is not None
        captured_engines.append(engine)
        return [
            TranslationResult(
                source=Path(path),
                destination=Path("build") / Path(path).name,
                chunks=1,
                voc={},
                format=TextFormat.PLAIN,
            )
        ]

    monkeypatch.setattr("abersetz.translate_path", fake_translate_path)
    monkeypatch.setattr("abersetz.config.load_config", lambda: advanced_api.AbersetzConfig())
    monkeypatch.setattr(sys, "argv", [str(module_path), "multi"])

    runpy.run_path(str(module_path), run_name="__main__")

    output = capsys.readouterr().out
    assert "Translating to es" in output
    assert captured_paths and captured_paths[0] == "docs"
    assert captured_engines and captured_engines[0] == "tr/google"


def test_advanced_api_cli_usage_banner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module_path = Path(__file__).resolve().parents[1] / "examples" / "advanced_api.py"
    monkeypatch.setattr(sys, "argv", [str(module_path)])
    monkeypatch.setattr("abersetz.config.load_config", lambda: advanced_api.AbersetzConfig())

    runpy.run_path(str(module_path), run_name="__main__")

    output = capsys.readouterr().out
    assert "Usage:" in output
    assert "Advanced examples:" in output
