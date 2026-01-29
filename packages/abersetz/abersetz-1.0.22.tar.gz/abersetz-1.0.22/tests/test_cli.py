"""CLI behaviour tests."""
# this_file: tests/test_cli.py

from __future__ import annotations

from pathlib import Path

import pytest
import tomllib

from abersetz.chunking import TextFormat
from abersetz.cli import (
    AbersetzCLI,
    _collect_engine_entries,
    _build_options_from_cli,
    _load_json_data,
    _parse_patterns,
    _render_engine_entries,
    _render_results,
    _render_validation_entries,
    abtr_main,
    main,
)
from abersetz.config import AbersetzConfig, Credential, Defaults, EngineConfig, save_config
from abersetz.pipeline import PipelineError, TranslationResult, TranslatorOptions
from abersetz.validation import ValidationResult


def test_cli_translate_wires_arguments(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: dict[str, object] = {}

    def fake_translate_path(path: str, options: TranslatorOptions):
        calls["path"] = path
        calls["options"] = options
        return []

    monkeypatch.setattr("abersetz.cli.translate_path", fake_translate_path)

    cli = AbersetzCLI()
    cli.tr(
        to_lang="es",
        path=str(tmp_path),
        engine="tr/google",
        include="*.txt,*.md",
        xclude="*.tmp",
        dry_run=True,
    )

    assert calls["path"] == str(tmp_path)
    opts = calls["options"]
    assert isinstance(opts, TranslatorOptions)
    assert opts.include == ("*.txt", "*.md")
    assert opts.xclude == ("*.tmp",)
    assert opts.dry_run is True


def test_cli_translate_accepts_path_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_translate_path(path: str | Path, options: TranslatorOptions):
        captured["path"] = Path(path)
        captured["options"] = options
        return []

    monkeypatch.setattr("abersetz.cli.translate_path", fake_translate_path)

    cli = AbersetzCLI()
    output_dir = tmp_path / "dest"
    cli.tr(
        to_lang="es",
        path=tmp_path,
        output=output_dir,
        engine="tr/google",
        dry_run=True,
    )

    opts_obj = captured["options"]
    assert isinstance(opts_obj, TranslatorOptions)
    assert isinstance(opts_obj.output_dir, Path)
    assert opts_obj.output_dir == output_dir.resolve()
    assert captured["path"] == tmp_path


def test_cli_accepts_legacy_engine_selector(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, TranslatorOptions] = {}

    def fake_translate_path(path: str, options: TranslatorOptions):
        captured["options"] = options
        return []

    monkeypatch.setattr("abersetz.cli.translate_path", fake_translate_path)

    cli = AbersetzCLI()
    cli.tr(to_lang="es", path=str(tmp_path), engine="translators/google", dry_run=True)

    opts = captured["options"]
    assert opts.engine == "tr/google"


def test_cli_translate_reports_pipeline_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: list[str] = []

    def fake_print(message: str) -> None:
        captured.append(message)

    def fake_translate_path(path: str, options: TranslatorOptions):
        raise PipelineError("failed to translate")

    monkeypatch.setattr("abersetz.cli.console.print", fake_print)
    monkeypatch.setattr("abersetz.cli.translate_path", fake_translate_path)

    cli = AbersetzCLI()
    with pytest.raises(PipelineError):
        cli.tr(to_lang="es", path=str(tmp_path), engine="tr/google")

    assert captured == ["[red]failed to translate[/red]"]


def test_parse_patterns_handles_none_and_iterables() -> None:
    assert _parse_patterns(None) == ()
    assert _parse_patterns("*.txt,  *.md ,, ") == ("*.txt", "*.md")
    assert _parse_patterns(("*.txt", "*.md")) == ("*.txt", "*.md")


def test_load_json_data_prefers_files(tmp_path: Path) -> None:
    data = {"greeting": "hello"}
    path = tmp_path / "data.json"
    path.write_text('{\n  "greeting": "hello"\n}')

    # when a path exists, it should be loaded from disk
    assert _load_json_data(str(path)) == data

    # inline JSON string should also be parsed
    assert _load_json_data('{"farewell": "bye"}') == {"farewell": "bye"}

    # empty references return empty dict for downstream safety
    assert _load_json_data(None) == {}


def test_build_options_requires_target_language(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Target language is required"):
        _build_options_from_cli(
            path=tmp_path,
            engine="tr/google",
            from_lang="auto",
            to_lang=None,
            recurse=True,
            write_over=False,
            output=None,
            save_voc=False,
            chunk_size=None,
            html_chunk_size=None,
            include=None,
            xclude=None,
            dry_run=True,
            prolog=None,
            voc=None,
        )


def test_build_options_loads_prolog_and_voc_json(tmp_path: Path) -> None:
    voc_path = tmp_path / "voc.json"
    voc_path.write_text('{"term": "gloss"}')

    options = _build_options_from_cli(
        path=tmp_path,
        engine="tr/google",
        from_lang="auto",
        to_lang="es",
        recurse=False,
        write_over=False,
        output=None,
        save_voc=False,
        chunk_size=None,
        html_chunk_size=None,
        include=None,
        xclude=None,
        dry_run=True,
        prolog='{"tone": "formal"}',
        voc=str(voc_path),
    )

    assert options.prolog == {"tone": "formal"}, "Expected inline prolog JSON to populate options"
    assert options.initial_voc == {"term": "gloss"}, "Expected voc file JSON to populate options"


def test_build_options_propagates_optional_flags(tmp_path: Path) -> None:
    options = _build_options_from_cli(
        path=tmp_path,
        engine="tr/google",
        from_lang="auto",
        to_lang="es",
        recurse=False,
        write_over=True,
        output=None,
        save_voc=True,
        chunk_size=900,
        html_chunk_size=1200,
        include=None,
        xclude=None,
        dry_run=True,
        prolog=None,
        voc=None,
    )

    assert options.save_voc is True, "Expected save_voc flag to propagate to options"
    assert options.write_over is True, "Expected write_over flag to propagate to options"
    assert options.chunk_size == 900, "Expected chunk_size override to propagate to options"
    assert options.html_chunk_size == 1200, "Expected html_chunk_size override to propagate"


def test_build_options_defaults_include_when_none(tmp_path: Path) -> None:
    options = _build_options_from_cli(
        path=tmp_path,
        engine="tr/google",
        from_lang="auto",
        to_lang="es",
        recurse=False,
        write_over=False,
        output=None,
        save_voc=False,
        chunk_size=None,
        html_chunk_size=None,
        include=None,
        xclude=None,
        dry_run=True,
        prolog=None,
        voc=None,
    )

    assert (
        options.include == TranslatorOptions().include
    ), "Expected include to fall back to TranslatorOptions defaults"


def test_build_options_resolves_output_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    options = _build_options_from_cli(
        path=tmp_path,
        engine="tr/google",
        from_lang="auto",
        to_lang="es",
        recurse=False,
        write_over=False,
        output=output_dir,
        save_voc=False,
        chunk_size=None,
        html_chunk_size=None,
        include=None,
        xclude=None,
        dry_run=True,
        prolog=None,
        voc=None,
    )

    assert options.output_dir == output_dir.resolve(), "Expected output_dir to resolve to absolute path"


def test_render_engine_entries_handles_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    import io

    from rich.console import Console

    buffer = io.StringIO()
    monkeypatch.setattr("abersetz.cli.console", Console(file=buffer, force_terminal=True))

    # Should show guidance for missing engines instead of crashing
    _render_engine_entries([])

    output = buffer.getvalue()
    assert "No engines detected." in output


def test_render_validation_entries_handles_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    import io

    from rich.console import Console

    buffer = io.StringIO()
    monkeypatch.setattr("abersetz.cli.console", Console(file=buffer, force_terminal=True))

    _render_validation_entries([])

    output = buffer.getvalue()
    assert "No engines available for validation." in output


def test_render_results_lists_destinations(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import io

    from rich.console import Console

    sink = io.StringIO()
    monkeypatch.setattr(
        "abersetz.cli.console",
        Console(
            file=sink,
            force_terminal=False,
            color_system=None,
            highlight=False,
            width=200,
        ),
    )

    result_one = TranslationResult(
        source=tmp_path / "en" / "sample.txt",
        destination=tmp_path / "pl" / "sample.txt",
        chunks=2,
        voc={},
        format=TextFormat.PLAIN,
        engine="tr/google",
        source_lang="en",
        target_lang="pl",
        chunk_size=1200,
    )
    result_two = TranslationResult(
        source=tmp_path / "en" / "other.txt",
        destination=tmp_path / "pl" / "other.txt",
        chunks=1,
        voc={},
        format=TextFormat.PLAIN,
        engine="tr/bing",
        source_lang="en",
        target_lang="pl",
        chunk_size=800,
    )

    _render_results([result_one, result_two])

    output = sink.getvalue()
    assert str(result_one.destination) in output
    assert str(result_two.destination) in output


@pytest.fixture
def _stub_engine_entries(monkeypatch: pytest.MonkeyPatch) -> AbersetzConfig:
    cfg = AbersetzConfig(
        defaults=Defaults(engine="tr/google"),
        engines={
            "translators": EngineConfig(
                name="translators", options={"provider": "bing", "providers": ["bing"]}
            ),
            "deep-translator": EngineConfig(
                name="deep-translator", options={"providers": ["deepl"]}
            ),
            "ullm": EngineConfig(
                name="ullm",
                options={
                    "profiles": {"default": {"model": "stub-default"}, "pro": {"model": "stub-pro"}}
                },
            ),
        },
    )

    monkeypatch.setattr("abersetz.cli.load_config", lambda: cfg)
    monkeypatch.setattr(
        "abersetz.cli.collect_translator_providers",
        lambda include_paid=False: ["bing", "google"]
        if not include_paid
        else ["bing", "google", "deepl"],
    )
    monkeypatch.setattr(
        "abersetz.cli.collect_deep_translator_providers",
        lambda include_paid=False: ["deepl", "argos"]
        if not include_paid
        else ["deepl", "argos", "papago"],
    )
    return cfg


def test_collect_engine_entries_handles_provider_strings(
    _stub_engine_entries: AbersetzConfig,
) -> None:
    entries = _collect_engine_entries(include_paid=False)
    selectors = [entry.selector for entry in entries]

    assert "tr/bing" in selectors
    assert "dt/deepl" in selectors
    assert "ll/default" in selectors
    assert "ll/pro" in selectors

    # family filter should narrow to ullm entries only
    ll_entries = _collect_engine_entries(include_paid=False, family="ll")
    assert {entry.selector for entry in ll_entries} == {"ll/default", "ll/pro"}

    # configured_only should skip discovered-but-unconfigured providers
    configured_entries = _collect_engine_entries(include_paid=False, configured_only=True)
    configured_selectors = {entry.selector for entry in configured_entries}
    assert "tr/google" not in configured_selectors
    assert "tr/bing" in configured_selectors
    assert "dt/deepl" in configured_selectors
    assert "ll/pro" in configured_selectors


def test_collect_engine_entries_family_accepts_long_name(
    _stub_engine_entries: AbersetzConfig,
) -> None:
    deep_entries = _collect_engine_entries(include_paid=False, family="deep-translator")
    selectors = {entry.selector for entry in deep_entries}
    assert selectors == {"dt", "dt/deepl", "dt/argos"}


def test_collect_engine_entries_configured_only_with_family(
    _stub_engine_entries: AbersetzConfig,
) -> None:
    paid_entries = _collect_engine_entries(
        include_paid=True,
        family="translators",
        configured_only=True,
    )
    selectors = {entry.selector for entry in paid_entries}
    assert selectors == {"tr", "tr/bing"}


def test_collect_engine_entries_accepts_single_provider_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = AbersetzConfig(
        defaults=Defaults(engine="tr/google"),
        engines={
            "translators": EngineConfig(name="translators", options={"provider": "bing"}),
            "deep-translator": EngineConfig(name="deep-translator"),
        },
    )

    monkeypatch.setattr("abersetz.cli.load_config", lambda: cfg)
    monkeypatch.setattr("abersetz.cli.collect_translator_providers", lambda include_paid=False: [])
    monkeypatch.setattr(
        "abersetz.cli.collect_deep_translator_providers", lambda include_paid=False: []
    )

    entries = _collect_engine_entries(include_paid=False)
    selectors = {entry.selector: entry for entry in entries}

    assert "tr/bing" in selectors
    assert selectors["tr/bing"].configured is True
    assert selectors["tr/bing"].requires_api_key is False


def test_collect_engine_entries_string_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = AbersetzConfig(
        defaults=Defaults(engine="tr/google"),
        engines={
            "translators": EngineConfig(
                name="translators",
                options={"providers": "bing"},
            ),
            "deep-translator": EngineConfig(
                name="deep-translator",
                options={"provider": "deepl"},
            ),
            "ullm": EngineConfig(name="ullm", options={"profiles": "default"}),
            "hysf": EngineConfig(name="hysf"),
        },
    )

    monkeypatch.setattr("abersetz.cli.load_config", lambda: cfg)
    monkeypatch.setattr("abersetz.cli.collect_translator_providers", lambda include_paid=False: [])
    monkeypatch.setattr(
        "abersetz.cli.collect_deep_translator_providers", lambda include_paid=False: []
    )

    entries = {entry.selector: entry for entry in _collect_engine_entries(include_paid=False)}

    assert entries["tr/bing"].configured is True
    assert entries["dt/deepl"].configured is True
    assert entries["ll/default"].configured is True
    assert entries["hy"].configured is True


def test_collect_engine_entries_includes_local_engines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = AbersetzConfig(
        defaults=Defaults(engine="tr/google"),
        engines={
            "mthy": EngineConfig(name="mthy", options={"backend": "mlx"}),
            "gemma": EngineConfig(name="gemma", options={"backend": "gguf"}),
        },
    )

    monkeypatch.setattr("abersetz.cli.load_config", lambda: cfg)
    monkeypatch.setattr("abersetz.cli.collect_translator_providers", lambda include_paid=False: [])
    monkeypatch.setattr(
        "abersetz.cli.collect_deep_translator_providers", lambda include_paid=False: []
    )

    entries = {entry.selector: entry for entry in _collect_engine_entries(include_paid=False)}

    assert entries["mthy/mlx"].configured is True
    assert entries["mthy/mlx"].requires_api_key is False
    assert entries["gemma/gguf"].configured is True


def test_collect_engine_entries_handles_deep_translator_string_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = AbersetzConfig(
        defaults=Defaults(engine="tr/google"),
        engines={
            "deep-translator": EngineConfig(
                name="deep-translator",
                options={"providers": "libre"},
            )
        },
    )

    monkeypatch.setattr("abersetz.cli.load_config", lambda: cfg)
    monkeypatch.setattr("abersetz.cli.collect_translator_providers", lambda include_paid=False: [])
    monkeypatch.setattr(
        "abersetz.cli.collect_deep_translator_providers", lambda include_paid=False: []
    )

    entries = {entry.selector: entry for entry in _collect_engine_entries(include_paid=False)}

    assert entries["dt/libre"].configured is True


def test_cli_config_commands_show_and_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_root = tmp_path / "cfg"
    monkeypatch.setenv("ABERSETZ_CONFIG_DIR", str(config_root))
    config = AbersetzConfig(
        defaults=Defaults(to_lang="pl", from_lang="en", engine="tr/google"),
        credentials={"api": Credential(name="api", value="secret")},
        engines={},
    )
    save_config(config)

    commands = AbersetzCLI().config()
    rendered = commands.show()
    parsed = tomllib.loads(rendered)

    assert parsed["defaults"]["to_lang"] == "pl"
    assert parsed["credentials"]["api"]["value"] == "secret"

    path = Path(commands.path())
    assert path == config_root / "config.toml"


def test_cli_lang_lists_languages(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []
    monkeypatch.setattr("abersetz.cli.console.print", lambda message: captured.append(str(message)))

    cli = AbersetzCLI()
    rows = cli.lang()

    assert captured  # ensure output emitted
    assert rows == captured
    assert rows[0].startswith("Popular targets:")
    assert rows[1].startswith("af\t")  # alphabetical by code


def test_cli_verbose_logs_translation_details(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class DummyLogger:
        def __init__(self) -> None:
            self.records: list[str] = []

        def remove(self) -> None:  # pragma: no cover - noop in tests
            return None

        def add(self, *args, **kwargs):  # pragma: no cover - noop in tests
            return 1

        def debug(self, message: str, *args, **kwargs) -> None:
            formatted = message.format(*args) if args else message
            self.records.append(formatted)

    dummy_logger = DummyLogger()
    monkeypatch.setattr("abersetz.cli.logger", dummy_logger, raising=False)

    sample_source = tmp_path / "input.txt"
    sample_destination = tmp_path / "pl" / "input.txt"
    result = TranslationResult(
        source=sample_source,
        destination=sample_destination,
        chunks=3,
        voc={},
        format=TextFormat.PLAIN,
        engine="tr/google",
        source_lang="auto",
        target_lang="pl",
        chunk_size=1200,
    )

    def fake_translate_path(path: str, options: TranslatorOptions):
        return [result]

    monkeypatch.setattr("abersetz.cli.translate_path", fake_translate_path)

    printed: list[str] = []
    monkeypatch.setattr("builtins.print", lambda value: printed.append(str(value)))

    cli = AbersetzCLI()
    cli.tr(
        to_lang="pl",
        path=str(sample_source),
        engine="tr/google",
        from_lang="auto",
        verbose=True,
    )

    assert dummy_logger.records == [
        f"Input: {sample_source}",
        "Engine: tr/google (from auto -> pl, chunk_size=1200, format=PLAIN)",
        "Chunks: 3",
        f"Output: {sample_destination}",
    ]
    assert printed == [str(sample_destination)]


def test_cli_engines_lists_configured_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AbersetzConfig(
        defaults=Defaults(engine="tr/google"),
        engines={
            "translators": EngineConfig(
                name="translators", options={"providers": ["google", "bing"]}
            ),
            "deep-translator": EngineConfig(
                name="deep-translator", options={"providers": ["google"]}
            ),
        },
    )

    monkeypatch.setattr("abersetz.cli.load_config", lambda: cfg)
    monkeypatch.setattr(
        "abersetz.cli.collect_translator_providers",
        lambda include_paid=False: ["google", "bing", "yandex"],
    )
    monkeypatch.setattr(
        "abersetz.cli.collect_deep_translator_providers",
        lambda include_paid=False: ["google"],
    )

    # Capture what's rendered
    import io

    from rich.console import Console

    output = io.StringIO()
    test_console = Console(file=output, force_terminal=True)
    monkeypatch.setattr("abersetz.cli.console", test_console)

    # The engines method no longer returns entries, just renders them
    AbersetzCLI().engines()

    # Check that the table was rendered with expected content
    table_output = output.getvalue()
    assert table_output  # ensure table rendered
    assert "tr/google" in table_output or "tr/go" in table_output  # Canonical short selector
    assert "dt/google" in table_output or "dt/go" in table_output
    assert "translators/" not in table_output


def test_cli_engines_supports_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AbersetzConfig(
        defaults=Defaults(engine="tr/google"),
        engines={
            "translators": EngineConfig(name="translators", options={"providers": ["google"]}),
            "deep-translator": EngineConfig(
                name="deep-translator", options={"providers": ["google"]}
            ),
        },
    )

    monkeypatch.setattr("abersetz.cli.load_config", lambda: cfg)
    monkeypatch.setattr(
        "abersetz.cli.collect_translator_providers",
        lambda include_paid=False: ["google", "bing"],
    )
    monkeypatch.setattr(
        "abersetz.cli.collect_deep_translator_providers",
        lambda include_paid=False: ["google", "deepl"],
    )

    import io

    from rich.console import Console

    def render(
        family: str | None = None, *, configured_only: bool = False, include_paid: bool = False
    ) -> str:
        output = io.StringIO()
        test_console = Console(file=output, force_terminal=True)
        monkeypatch.setattr("abersetz.cli.console", test_console)
        cli = AbersetzCLI()
        cli.engines(include_paid, family=family, configured_only=configured_only)
        return output.getvalue()

    family_output = render(family="dt")
    assert "dt/google" in family_output
    assert "tr/google" not in family_output

    configured_output = render(configured_only=True)
    assert "tr/google" in configured_output
    assert "tr/bing" not in configured_output


def test_cli_validate_renders_results(monkeypatch: pytest.MonkeyPatch) -> None:
    import io

    from rich.console import Console

    output = io.StringIO()
    test_console = Console(file=output, force_terminal=True)
    monkeypatch.setattr("abersetz.cli.console", test_console)

    results = [
        ValidationResult(
            selector="tr/google", success=True, translation="Hola", error=None, latency=0.12
        ),
        ValidationResult(
            selector="ll/default",
            success=False,
            translation="",
            error="EngineError: missing profile",
            latency=0.05,
        ),
    ]

    monkeypatch.setattr("abersetz.cli.validate_engines", lambda cfg, **kwargs: results)
    monkeypatch.setattr("abersetz.cli.load_config", lambda: AbersetzConfig())

    cli = AbersetzCLI()
    returned = cli.validate()

    assert returned == results
    rendered = output.getvalue()
    assert "tr/google" in rendered
    assert "ll/default" in rendered
    assert "✓" in rendered
    assert "✗" in rendered


def test_cli_validate_accepts_selector_string(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_validate(config: AbersetzConfig, **kwargs: object):
        captured_kwargs.update(kwargs)
        return []

    monkeypatch.setattr("abersetz.cli.validate_engines", fake_validate)
    monkeypatch.setattr("abersetz.cli.load_config", lambda: AbersetzConfig())

    cli = AbersetzCLI()
    cli.validate(selectors="tr/google,ll/default", include_defaults=False)

    assert captured_kwargs["selectors"] == ("tr/google", "ll/default")
    assert captured_kwargs["include_defaults"] is False


def test_cli_setup_forwards_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[bool, bool]] = []

    def fake_setup_command(*, non_interactive: bool, verbose: bool) -> None:
        calls.append((non_interactive, verbose))

    monkeypatch.setattr("abersetz.cli.setup_command", fake_setup_command)

    cli = AbersetzCLI()
    cli.setup(non_interactive=True, verbose=True)

    assert calls == [(True, True)]


def test_cli_main_invokes_fire(monkeypatch: pytest.MonkeyPatch) -> None:
    invoked: list[object] = []

    def fake_fire(target: object, *args: object, **kwargs: object) -> None:
        invoked.append(target)

    monkeypatch.setattr("abersetz.cli.fire.Fire", fake_fire)

    main()

    assert len(invoked) == 1
    assert isinstance(invoked[0], AbersetzCLI)


def test_cli_abtr_main_invokes_fire_with_tr(monkeypatch: pytest.MonkeyPatch) -> None:
    invoked: list[object] = []

    def fake_fire(target: object, *args: object, **kwargs: object) -> None:
        invoked.append(target)

    monkeypatch.setattr("abersetz.cli.fire.Fire", fake_fire)

    abtr_main()

    assert len(invoked) == 1
    bound = invoked[0]
    assert callable(bound)
    assert getattr(bound, "__self__", None).__class__ is AbersetzCLI
    assert getattr(bound, "__func__", None) is AbersetzCLI.tr
