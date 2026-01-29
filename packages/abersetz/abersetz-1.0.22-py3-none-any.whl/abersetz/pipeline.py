"""High level translation pipeline."""
# this_file: src/abersetz/pipeline.py

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from .chunking import TextFormat, chunk_text, detect_format
from .config import AbersetzConfig, load_config
from .engine_catalog import normalize_selector
from .engines import Engine, EngineRequest, EngineResult, create_engine

DEFAULT_PATTERNS = ("*.txt", "*.md", "*.mdx", "*.html", "*.htm")


@dataclass(slots=True)
class TranslatorOptions:
    """Runtime options controlling translation behaviour."""

    engine: str | None = None
    from_lang: str | None = None
    to_lang: str | None = None
    recurse: bool = True
    write_over: bool = False
    output_dir: Path | None = None
    save_voc: bool = False
    chunk_size: int | None = None
    html_chunk_size: int | None = None
    include: tuple[str, ...] = DEFAULT_PATTERNS
    xclude: tuple[str, ...] = tuple()
    dry_run: bool = False
    prolog: dict[str, str] = field(default_factory=dict)
    initial_voc: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class TranslationResult:
    """Information about a translated artefact."""

    source: Path
    destination: Path
    chunks: int
    voc: dict[str, str]
    format: TextFormat
    engine: str = ""
    source_lang: str = ""
    target_lang: str = ""
    chunk_size: int = 0


class PipelineError(RuntimeError):
    """Raised when translation cannot proceed."""


def translate_path(
    path: Path | str,
    options: TranslatorOptions | None = None,
    *,
    config: AbersetzConfig | None = None,
    client: object | None = None,
) -> list[TranslationResult]:
    """Translate a file or directory tree."""
    resolved = Path(path).resolve()

    # Validate input path exists and is accessible
    if not resolved.exists():
        raise PipelineError(f"Path does not exist: {resolved}")

    # Check readability
    try:
        if resolved.is_file():
            # Try to open the file to check read permissions
            resolved.open("r").close()
        elif resolved.is_dir():
            # Try to list directory to check read permissions
            list(resolved.iterdir())
    except (PermissionError, OSError) as e:
        raise PipelineError(f"Cannot read {resolved}: {e}")

    cfg = config or load_config()
    opts = _merge_defaults(options, cfg)
    targets = list(_discover_files(resolved, opts))
    if not targets:
        raise PipelineError(f"No files matched under {resolved}")
    engine_selector = normalize_selector(opts.engine or cfg.defaults.engine) or cfg.defaults.engine
    engine = create_engine(engine_selector, cfg, client=client)
    results: list[TranslationResult] = []

    # Simple translation without progress bar
    for file_path in targets:
        result = _translate_file(file_path, engine, opts, cfg)
        results.append(result)

    return results


def _merge_defaults(options: TranslatorOptions | None, config: AbersetzConfig) -> TranslatorOptions:
    opts = options or TranslatorOptions()
    if opts.engine is None:
        opts.engine = config.defaults.engine
    else:
        normalized_engine = normalize_selector(opts.engine)
        if normalized_engine:
            opts.engine = normalized_engine
    if opts.from_lang is None:
        opts.from_lang = config.defaults.from_lang
    if opts.to_lang is None:
        opts.to_lang = config.defaults.to_lang
    if opts.chunk_size is None:
        opts.chunk_size = config.defaults.chunk_size
    if opts.html_chunk_size is None:
        opts.html_chunk_size = config.defaults.html_chunk_size
    return opts


def _discover_files(root: Path, opts: TranslatorOptions) -> Iterable[Path]:
    if root.is_file():
        return [root]
    pattern_iter = root.rglob if opts.recurse else root.glob
    matched: list[Path] = []
    for pattern in opts.include:
        matched.extend(pattern_iter(pattern))
    filtered = [path for path in matched if not _is_xcluded(path, opts.xclude)]
    return sorted({path.resolve() for path in filtered if path.is_file()})


def _is_xcluded(path: Path, patterns: tuple[str, ...]) -> bool:
    return any(path.match(pattern) for pattern in patterns)


def _translate_file(
    source: Path,
    engine: Engine,
    opts: TranslatorOptions,
    config: AbersetzConfig,
) -> TranslationResult:
    text = source.read_text(encoding="utf-8")

    engine_selector = opts.engine or config.defaults.engine
    engine_selector = normalize_selector(engine_selector) or engine_selector
    source_lang = opts.from_lang or config.defaults.from_lang
    target_lang = opts.to_lang or config.defaults.to_lang

    # Handle edge cases
    if not text.strip():
        # Empty file - just create an empty output
        destination = _persist_output(
            source,
            "",
            {},
            TextFormat.PLAIN,
            opts,
            opts.to_lang or config.defaults.to_lang,
        )
        return TranslationResult(
            source=source,
            destination=destination,
            chunks=0,
            voc={},
            format=TextFormat.PLAIN,
            engine=engine_selector,
            source_lang=source_lang,
            target_lang=target_lang,
            chunk_size=0,
        )

    # Warn about very large files (>10MB)
    file_size = source.stat().st_size
    if file_size > 10 * 1024 * 1024:  # 10MB
        from loguru import logger

        logger.warning(f"Large file detected ({file_size / 1024 / 1024:.1f}MB): {source}")

    fmt = detect_format(text)
    chunk_size = _select_chunk_size(fmt, engine, opts, config)
    chunks = chunk_text(text, chunk_size, fmt)
    # logger.debug("%s: %s chunk(s) of size %s", source, len(chunks) or 1, chunk_size)
    results, voc = _apply_engine(engine, chunks, fmt, opts, config)
    merged_text = "".join(item.text for item in results)
    destination = _persist_output(
        source,
        merged_text,
        voc,
        fmt,
        opts,
        opts.to_lang or config.defaults.to_lang,
    )
    return TranslationResult(
        source=source,
        destination=destination,
        chunks=len(chunks) or 1,
        voc=voc,
        format=fmt,
        engine=engine_selector,
        source_lang=source_lang,
        target_lang=target_lang,
        chunk_size=chunk_size,
    )


def _apply_engine(
    engine: Engine,
    chunks: Iterable[str],
    fmt: TextFormat,
    opts: TranslatorOptions,
    config: AbersetzConfig,
) -> tuple[list[EngineResult], dict[str, str]]:
    voc = dict(opts.initial_voc)
    prolog = dict(opts.prolog)
    results: list[EngineResult] = []
    chunk_list = list(chunks)
    total = len(chunk_list) or 1
    for index, chunk in enumerate(chunk_list):
        # logger.debug("Engine %s chunk %s/%s", engine.name, index + 1, total)
        request = _build_request(chunk, index, total, fmt, opts, config, voc, prolog)
        result = engine.translate(request)
        voc = result.voc
        results.append(result)
    return results, voc


def _build_request(
    chunk: str,
    index: int,
    total: int,
    fmt: TextFormat,
    opts: TranslatorOptions,
    config: AbersetzConfig,
    voc: dict[str, str],
    prolog: dict[str, str],
) -> EngineRequest:
    return EngineRequest(
        text=chunk,
        source_lang=opts.from_lang or "auto",
        target_lang=opts.to_lang or config.defaults.to_lang,
        is_html=fmt is TextFormat.HTML,
        voc=voc,
        prolog=prolog,
        chunk_index=index,
        total_chunks=total,
    )


def _select_chunk_size(
    fmt: TextFormat,
    engine: Engine,
    opts: TranslatorOptions,
    config: AbersetzConfig,
) -> int:
    if fmt is TextFormat.HTML:
        html_size = (
            opts.html_chunk_size or engine.chunk_size_for(fmt) or config.defaults.html_chunk_size
        )
        return max(html_size, 1)
    plain_size = opts.chunk_size or engine.chunk_size_for(fmt) or config.defaults.chunk_size
    return max(plain_size, 1)


def _persist_output(
    source: Path,
    content: str,
    voc: dict[str, str],
    fmt: TextFormat,
    opts: TranslatorOptions,
    target_lang: str,
) -> Path:
    if opts.write_over:
        destination = source
    else:
        base = opts.output_dir or source.parent / target_lang
        base.mkdir(parents=True, exist_ok=True)
        destination = base / source.name
    if not opts.dry_run:
        destination.write_text(content, encoding="utf-8")
        if opts.save_voc:
            vocab_path = destination.with_suffix(destination.suffix + ".voc.json")
            vocab_path.write_text(json.dumps(voc, indent=2, ensure_ascii=False), encoding="utf-8")
    return destination


__all__ = [
    "PipelineError",
    "TranslationResult",
    "TranslatorOptions",
    "translate_path",
]
