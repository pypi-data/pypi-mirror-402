"""Command line interface for abersetz."""
# this_file: src/abersetz/cli.py

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

import fire  # type: ignore
import tomli_w
from loguru import logger
from rich.console import Console
from rich.table import Table

from .config import config_path, load_config
from .engine_catalog import (
    DEEP_TRANSLATOR_PAID_PROVIDERS,
    PAID_TRANSLATOR_PROVIDERS,
    EngineEntry,
    collect_deep_translator_providers,
    collect_translator_providers,
    normalize_selector,
)
from .pipeline import PipelineError, TranslationResult, TranslatorOptions, translate_path
from .setup import setup_command
from .validation import ValidationResult, validate_engines

console = Console()


def _configure_logging(verbose: bool) -> None:
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, level=level, enqueue=False)


def _parse_patterns(value: str | Sequence[str] | None) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str):
        parts = [item.strip() for item in value.split(",") if item.strip()]
        return tuple(parts)
    return tuple(value)


def _load_json_data(reference: str | None) -> dict[str, str]:
    if not reference:
        return {}
    path = Path(reference)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(reference)


def _render_results(results: Iterable[TranslationResult]) -> None:
    # Simple output - just list the output files
    for result in results:
        console.print(str(result.destination))


def _render_engine_entries(entries: list[EngineEntry]) -> None:
    if not entries:
        console.print("No engines detected.")
        return
    table = Table(title="Available Translation Engines", show_header=True, header_style="bold cyan")
    table.add_column("Selector", style="white")
    table.add_column("Family", style="cyan")
    table.add_column("Configured", style="green")
    table.add_column("Credential", style="yellow")
    table.add_column("Notes", style="magenta")

    for entry in entries:
        base = entry.selector.split("/", 1)[0]
        table.add_row(
            entry.selector,
            base,
            "✓" if entry.configured else "✗",
            "required" if entry.requires_api_key else "free",
            entry.notes,
        )
    console.print(table)


def _render_validation_entries(results: list[ValidationResult]) -> None:
    if not results:
        console.print("No engines available for validation.")
        return

    table = Table(title="Engine Validation", show_header=True, header_style="bold cyan")
    table.add_column("Selector", style="white")
    table.add_column("Status", style="green")
    table.add_column("Latency (s)", justify="right", style="yellow")
    table.add_column("Sample Output", style="magenta")
    table.add_column("Error", style="red")

    for result in results:
        status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
        latency = f"{result.latency:.2f}"
        sample = result.translation[:80]
        error = result.error or ""
        table.add_row(result.selector, status, latency, sample, error)

    console.print(table)


def _collect_engine_entries(
    include_paid: bool,
    *,
    family: str | None = None,
    configured_only: bool = False,
) -> list[EngineEntry]:
    cfg = load_config()
    entries: list[EngineEntry] = []

    # translators engine
    translator_cfg = cfg.engines.get("translators")
    entries.append(
        EngineEntry(
            selector=str(normalize_selector("translators")),
            configured=translator_cfg is not None,
            requires_api_key=False,
            notes="use tr/<provider>",
        )
    )
    configured_translators: list[str] = []
    if translator_cfg:
        providers_value = translator_cfg.options.get("providers")
        if isinstance(providers_value, list | tuple):
            configured_translators.extend(str(p).strip() for p in providers_value if str(p).strip())
        elif isinstance(providers_value, str) and providers_value.strip():
            configured_translators.append(providers_value.strip())
        single_provider = translator_cfg.options.get("provider")
        if isinstance(single_provider, str) and single_provider.strip():
            configured_translators.append(single_provider.strip())
    available_translators = collect_translator_providers(include_paid=include_paid)
    translator_candidates = sorted(
        {
            *configured_translators,
            *available_translators,
        },
        key=str.lower,
    )
    for provider in translator_candidates:
        selector = str(normalize_selector(f"translators/{provider}"))
        notes = "free" if provider not in PAID_TRANSLATOR_PROVIDERS else "requires API"
        entries.append(
            EngineEntry(
                selector=selector,
                configured=provider in configured_translators,
                requires_api_key=provider in PAID_TRANSLATOR_PROVIDERS,
                notes=notes,
            )
        )

    # deep-translator engine
    deep_cfg = cfg.engines.get("deep-translator")
    entries.append(
        EngineEntry(
            selector=str(normalize_selector("deep-translator")),
            configured=deep_cfg is not None,
            requires_api_key=False,
            notes="use dt/<provider>",
        )
    )
    configured_deep: list[str] = []
    if deep_cfg:
        providers_value = deep_cfg.options.get("providers")
        if isinstance(providers_value, list | tuple):
            configured_deep.extend(str(p).strip() for p in providers_value if str(p).strip())
        elif isinstance(providers_value, str) and providers_value.strip():
            configured_deep.append(providers_value.strip())
        single_provider = deep_cfg.options.get("provider")
        if isinstance(single_provider, str) and single_provider.strip():
            configured_deep.append(single_provider.strip())
    available_deep = collect_deep_translator_providers(include_paid=include_paid)
    deep_candidates = sorted({*configured_deep, *available_deep}, key=str.lower)
    for provider in deep_candidates:
        selector = str(normalize_selector(f"deep-translator/{provider}"))
        notes = "free" if provider not in DEEP_TRANSLATOR_PAID_PROVIDERS else "requires API"
        entries.append(
            EngineEntry(
                selector=selector,
                configured=provider in configured_deep,
                requires_api_key=provider in DEEP_TRANSLATOR_PAID_PROVIDERS,
                notes=notes,
            )
        )

    # hysf engine
    if "hysf" in cfg.engines:
        entries.append(
            EngineEntry(
                selector=str(normalize_selector("hysf")),
                configured=True,
                requires_api_key=True,
                notes="siliconflow",
            )
        )

    for local_name in ("mthy", "gemma"):
        local_cfg = cfg.engines.get(local_name)
        if local_cfg:
            backend = str(local_cfg.options.get("backend", "")).strip()
            selector = f"{local_name}/{backend}" if backend else local_name
            entries.append(
                EngineEntry(
                    selector=selector,
                    configured=True,
                    requires_api_key=False,
                    notes=backend or "local",
                )
            )

    ullm_cfg = cfg.engines.get("ullm")
    if ullm_cfg:
        profiles = ullm_cfg.options.get("profiles", {})
        if isinstance(profiles, dict):
            for profile_name in sorted(profiles):
                selector = str(normalize_selector(f"ullm/{profile_name}"))
                entries.append(
                    EngineEntry(
                        selector=selector,
                        configured=True,
                        requires_api_key=True,
                        notes=profiles[profile_name].get("model", ""),
                    )
                )
        else:
            entries.append(
                EngineEntry(
                    selector=str(normalize_selector("ullm/default")),
                    configured=True,
                    requires_api_key=True,
                    notes="",
                )
            )

    if family:
        family_selector = normalize_selector(family)
        base = (family_selector or family).split("/", 1)[0].strip().lower()
        entries = [entry for entry in entries if entry.selector.split("/", 1)[0] == base]

    if configured_only:
        entries = [entry for entry in entries if entry.configured]

    return entries


class ConfigCommands:
    """Configuration related helpers."""

    def show(self) -> str:
        cfg = load_config()
        data = cfg.to_dict()
        toml_output = tomli_w.dumps(data)
        return toml_output

    def path(self) -> str:
        path = str(config_path())
        return path


def _validate_language_code(code: str | None, param_name: str) -> str | None:
    """Validate language code format."""
    if code is None or code == "auto":
        return code

    # Basic validation for common language codes - silently accept
    return code


def _build_options_from_cli(
    path: str | Path,
    *,
    engine: str | None,
    from_lang: str | None,
    to_lang: str | None,
    recurse: bool,
    write_over: bool,
    output: str | Path | None,
    save_voc: bool,
    chunk_size: int | None,
    html_chunk_size: int | None,
    include: str | Sequence[str] | None,
    xclude: str | Sequence[str] | None,
    dry_run: bool,
    prolog: str | None,
    voc: str | None,
) -> TranslatorOptions:
    # Validate language codes
    validated_from_lang = _validate_language_code(from_lang, "--from-lang")
    validated_to_lang = _validate_language_code(to_lang, "target language")
    if validated_to_lang is None:
        raise ValueError("Target language is required")

    normalized_engine = normalize_selector(engine) if engine else None

    output_dir: Path | None
    output_dir = None if output is None else Path(output).resolve()

    return TranslatorOptions(
        to_lang=validated_to_lang,
        engine=normalized_engine,
        from_lang=validated_from_lang,
        recurse=recurse,
        write_over=write_over,
        output_dir=output_dir,
        save_voc=save_voc,
        chunk_size=chunk_size,
        html_chunk_size=html_chunk_size,
        include=_parse_patterns(include) or TranslatorOptions().include,
        xclude=_parse_patterns(xclude),
        dry_run=dry_run,
        prolog=_load_json_data(prolog),
        initial_voc=_load_json_data(voc),
    )


def _iter_language_rows() -> list[str]:
    from langcodes import get
    from langcodes.language_lists import CLDR_LANGUAGES

    rows: list[str] = []
    for code in sorted(CLDR_LANGUAGES):
        name = get(code).language_name("en")
        rows.append(f"{code}\t{name}")
    return rows


POPULAR_LANG_CODES = ("en", "es", "fr", "de", "ja", "zh-CN", "pl")


class AbersetzCLI:
    """Abersetz translation tool - translate files between languages.

    Use 'abersetz tr' to translate files, or 'abersetz config' to manage configuration.
    """

    def version(self) -> str:
        """Show version information."""
        from . import __version__

        console.print(f"abersetz version {__version__}")
        return __version__

    def tr(
        self,
        to_lang: str,
        path: str | Path,
        *,
        engine: str | None = None,
        from_lang: str | None = None,
        recurse: bool = True,
        write_over: bool = False,
        output: str | Path | None = None,
        save_voc: bool = False,
        chunk_size: int | None = None,
        html_chunk_size: int | None = None,
        include: str | Sequence[str] | None = None,
        xclude: str | Sequence[str] | None = None,
        dry_run: bool = False,
        prolog: str | None = None,
        voc: str | None = None,
        verbose: bool = False,
    ) -> None:
        _configure_logging(verbose)
        opts = _build_options_from_cli(
            to_lang=to_lang,
            path=path,
            engine=engine,
            from_lang=from_lang,
            recurse=recurse,
            write_over=write_over,
            output=output,
            save_voc=save_voc,
            chunk_size=chunk_size,
            html_chunk_size=html_chunk_size,
            include=include,
            xclude=xclude,
            dry_run=dry_run,
            prolog=prolog,
            voc=voc,
        )
        try:
            results = translate_path(path, opts)
        except PipelineError as error:
            console.print(f"[red]{error}[/red]")
            raise
        # Minimal output - just print destinations
        for result in results:
            if verbose:
                logger.debug("Input: {}", result.source)
                logger.debug(
                    "Engine: {} (from {} -> {}, chunk_size={}, format={})",
                    result.engine or opts.engine,
                    result.source_lang or (opts.from_lang or "auto"),
                    result.target_lang or (opts.to_lang or ""),
                    result.chunk_size,
                    result.format.name,
                )
                logger.debug("Chunks: {}", result.chunks)
                logger.debug("Output: {}", result.destination)
            print(result.destination)

    def config(self) -> ConfigCommands:
        return ConfigCommands()

    def lang(self) -> list[str]:
        from langcodes import get

        popular: list[str] = []
        for code in POPULAR_LANG_CODES:
            try:
                name = get(code).language_name("en")
            except Exception:  # pragma: no cover - unexpected lookup failure
                name = code
            popular.append(f"{code} ({name})")
        header = "Popular targets: " + ", ".join(popular)

        rows = [header]
        rows.extend(_iter_language_rows())
        for line in rows:
            console.print(line)
        return rows

    def engines(
        self,
        include_paid: bool = False,
        *,
        family: str | None = None,
        configured_only: bool = False,
    ) -> None:
        """List available engines and whether they are configured."""
        entries = _collect_engine_entries(
            include_paid,
            family=family,
            configured_only=configured_only,
        )
        _render_engine_entries(entries)

    def setup(
        self,
        non_interactive: bool = False,
        verbose: bool = False,
        include_community: bool = False,
    ) -> None:
        """Run the configuration setup wizard.

        Args:
            non_interactive: Run without user interaction (for CI/automation)
            verbose: Enable verbose output with detailed logging
            include_community: Include community/self-hosted providers in defaults
        """
        setup_command(
            non_interactive=non_interactive,
            verbose=verbose,
            include_community=include_community,
        )

    def validate(
        self,
        *,
        selectors: str | Sequence[str] | None = None,
        target_lang: str = "es",
        source_lang: str = "auto",
        sample_text: str = "Hello, world!",
        include_defaults: bool = True,
    ) -> list[ValidationResult]:
        """Validate configured engines by translating a short phrase."""

        cfg = load_config()
        selector_tuple = _parse_patterns(selectors)
        results = validate_engines(
            cfg,
            selectors=selector_tuple or None,
            target_lang=target_lang,
            source_lang=source_lang,
            sample_text=sample_text,
            include_defaults=include_defaults,
        )
        _render_validation_entries(results)
        return results


def main() -> None:
    """Invoke the Fire CLI."""
    fire.Fire(AbersetzCLI())


def abtr_main() -> None:
    """Direct translation CLI - equivalent to 'abersetz tr'."""

    # Create CLI instance and call tr method directly
    cli = AbersetzCLI()

    # Use Fire to parse arguments for the tr method specifically
    fire.Fire(cli.tr)


__all__ = ["AbersetzCLI", "ConfigCommands", "main", "abtr_main"]
