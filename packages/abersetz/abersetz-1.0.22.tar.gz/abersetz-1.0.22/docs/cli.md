---
layout: default
title: CLI Reference
nav_order: 3
---

# CLI Reference
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

Abersetz ships with two command-line tools:

- `abersetz`: The main interface. Supports subcommands like `tr`, `validate`, `config`, `engines`, and `version`.
- `abtr`: A shorthand for direct translation.

## Main Commands

### abersetz tr

Translate files or directories.

```bash
abersetz tr PATH [OPTIONS]
```

#### Arguments

- `PATH`: File or directory to translate (required)

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `to_lang` (positional) | Target language code | — |
| `--from-lang` | Source language code | `auto` |
| `--engine` | Translation engine | `tr/google` |
| `--output` | Output directory | `<lang>/<filename>` |
| `--recurse/--no-recurse` | Process subdirectories | `True` |
| `--write_over` | Replace original files | `False` |
| `--include` | File patterns to include | `*.txt,*.md,*.html` |
| `--xclude` | File patterns to exclude | None |
| `--chunk-size` | Characters per chunk | `1200` |
| `--html-chunk-size` | Characters per HTML chunk | `1800` |
| `--save-voc` | Save vocabulary JSON | `False` |
| `--dry-run` | Preview without translating | `False` |
| `--verbose` | Enable debug output | `False` |

### abersetz config

Manage configuration settings.

```bash
abersetz config COMMAND
```

#### Subcommands

- `show`: Show current configuration
- `path`: Show config file location

### abersetz version

Show version info.

```bash
abersetz version
```

### abersetz engines

List available engine families and providers.

```bash
abersetz engines [--include-paid] [--family tr|dt|ll|hy] [--configured-only]
```

- `--family`: Filter by engine family.
- `--configured-only`: List only configured engines.

### abersetz setup

Run the configuration setup wizard.

```bash
abersetz setup [--non-interactive] [--verbose] [--include-community]
```

- `--non-interactive`: Run without prompts (CI/automation).
- `--verbose`: Enable verbose debug logging.
- `--include-community`: Add community/self-hosted providers such as LibreTranslate to defaults.

### abersetz validate

Test each configured engine with a short translation. Reports status, latency, and pricing info.

```bash
abersetz validate [--selectors tr/google,ll/default] [--target-lang es] [--sample-text "Hello"]
```

- `--selectors`: Comma-separated list of engines to test. Defaults to all configured.
- `--target-lang`: Language for test translation. Defaults to `es`.
- `--sample-text`: Custom text for testing. Defaults to `"Hello, world!"`.
- `--include-defaults/--no-include-defaults`: Include default engine from config. Default is `True`.

{: .note }
Validation uses live APIs. To avoid hitting every configured engine, use `--selectors` and `--no-include-defaults`. Example:

```bash
abersetz validate \
  --selectors tr/google,ll/default \
  --no-include-defaults \
  --sample-text "Ping"
```

This tests Google Translate and your primary LLM profile quickly, skipping offline or throttled engines.

## Shorthand Command

### abtr

Shorthand for `abersetz tr`.

```bash
abtr TO_LANG PATH [OPTIONS]
```

Supports all the same options as `abersetz tr`.

## Usage Examples

### Basic Translation

Translate a single file to Spanish:

```bash
abersetz tr es document.txt
```

Same using shorthand:

```bash
abtr fr document.txt
```

### Directory Translation

Translate all files in `./docs` to German:

```bash
abersetz tr de ./docs --output ./docs_de
```

With custom include/exclude patterns:

```bash
abtr ja ./project \
  --include "*.md,*.txt" \
  --xclude "*test*,.*" \
  --output ./translations/ja
```

### Engine Selection

Use different translation engines:

```bash
# Google Translate (free)
abtr pt file.txt --engine translators/google

# Bing Translate (free)
abtr pt file.txt --engine translators/bing

# DeepL
abtr pt file.txt --engine deep-translator/deepl

# SiliconFlow LLM
abtr pt file.txt --engine hysf

# Custom LLM profile
abtr pt file.txt --engine ullm/gpt4
```

### Validate Engines

Check health of specific engines:

```bash
abersetz validate --target-lang de --selectors tr/google,ll/default
```

### Advanced Options

Overwrite original files:

```bash
abersetz tr es backup.txt --write_over
```

Save vocabulary file for LLM engines:

```bash
abtr de technical.md \
  --engine ullm/default \
  --save-voc
```

Preview changes without translating:

```bash
abersetz tr fr large_project/ \
  --dry-run
```

Custom chunk sizes for HTML:

```bash
abtr zh-CN document.html \
  --html-chunk-size 3000
```

## Language Codes

Supported language codes:

| Code | Language |
|------|----------|
| `en` | English |
| `es` | Spanish |
| `fr` | French |
| `de` | German |
| `it` | Italian |
| `pt` | Portuguese |
| `ru` | Russian |
| `ja` | Japanese |
| `ko` | Korean |
| `zh-CN` | Chinese (Simplified) |
| `zh-TW` | Chinese (Traditional) |
| `ar` | Arabic |
| `hi` | Hindi |
| `auto` | Auto-detect (source only) |

## Pattern Matching

Include/exclude patterns support wildcards:

- `*.txt` – All .txt files
- `doc*` – Files starting with "doc"
- `*test*` – Files containing "test"
- `.*` – Hidden files
- `*.{md,txt}` – Files with .md or .txt extension

## Environment Variables

Set defaults via environment variables:

```bash
# Default target language
export ABERSETZ_TO_LANG=es

# Default engine
export ABERSETZ_ENGINE=translators/bing

# API keys for LLM engines
export OPENAI_API_KEY=sk-...
export SILICONFLOW_API_KEY=sk-...
```

## Output Format

Translation outputs are printed as file paths:

```
/path/to/output/file1.txt
/path/to/output/file2.txt
```

Add `--verbose` for detailed progress logs:

```bash
abersetz tr fr docs/ --verbose
```

## Error Handling

Common errors and fixes:

### Missing API key

```
Error: Missing API key for engine
```

Fix: Set the required environment variable:

```bash
export SILICONFLOW_API_KEY="your-key"
```

### No files matched

```
Error: No files matched under /path
```

Fix: Review include patterns:

```bash
abtr . --include "*.md,*.txt"
```

### Network error

```
Error: Network error - Connection timeout
```

Fix: Tool retries automatically. Check your connection.

## Tips and Tricks

### Batch translation

Translate to multiple languages with a loop:

```bash
for lang in es fr de ja; do
  abersetz tr $lang docs/ --output docs_$lang
done
```

### Parallel processing

Speed up translation with GNU parallel:

```bash
find . -name "*.txt" | parallel -j4 abtr es {}
```

### Progress tracking

Log progress for large jobs:

```bash
abersetz tr fr large_project/ --verbose 2>&1 | tee translation.log
```

### Testing configuration

Always preview with `--dry-run`:

```bash
abersetz tr de important_docs/ --dry-run
```

## See Also

- [Configuration Guide](configuration/)
- [Python API Reference](api/)
- [Translation Engines](engines/)
