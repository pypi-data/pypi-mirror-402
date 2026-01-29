# abersetz

A minimalist file translator that uses established machine translation engines while keeping configuration portable and repeatable. It follows a simple pipeline: locate → chunk → translate → merge. Provides both a Python API and a CLI powered by `fire`.

## Why abersetz?

- Translates files, not just strings.
- Supports engines from `translators`, `deep-translator`, and pluggable LLM-based backends for consistent terminology.
- Stores engine preferences and credentials using `platformdirs`, supporting either raw values or environment variables.
- Shares vocabulary across chunks to maintain consistency in long documents.
- Keeps the codebase small: no custom infrastructure, just clear components doing their job.

## Key Features

- Recursive file discovery with include/exclude filters.
- Automatic HTML vs. plain-text detection to preserve markup where possible.
- Semantic chunking via `semantic-text-splitter`, with per-engine configurable lengths.
- Vocabulary-aware translation pipeline that merges `<voc>` JSON output from LLM engines.
- Dry-run mode for offline testing and demos.
- Optional vocabulary sidecar files when `--save-voc` is enabled.
- Built-in `abersetz validate` command that pings configured engines, reports latency, and shows pricing hints from the research catalog.
- Optional local MLX/GGUF engines for HY-MT and TranslateGemma when configured (`mthy`, `gemma`).

## Installation

```bash
pip install abersetz
```

## Quick Start

### First-time Setup

```bash
# Auto-discover and configure available translation services
abersetz setup

# Test configured engines with a quick validation
abersetz validate --target-lang es
```

Use `abersetz setup --include-community` to include community/self-hosted engines like LibreTranslate in the defaults.

This scans your environment for API keys, tests endpoints, and generates an optimized config.

### Basic Translation

```bash
# Translate using main CLI
abersetz tr pl ./docs --engine tr/google --output ./build/pl

# Or use the shorthand
abtr pl ./docs --engine tr/google --output ./build/pl
```

### CLI Options

- `to_lang`: First positional argument specifying target language.
- `--from-lang`: Source language (default: `auto`).
- `--engine`: One of:
  - `tr/<provider>` (e.g., `tr/google`)
  - `dt/<provider>` (e.g., `dt/deepl`)
  - `hy`
  - `ll/<profile>` where profiles are defined in config.
    - Legacy selectors like `translators/google` still work and are auto-normalized.
- `--recurse/--no-recurse`: Traverse subdirectories (default: on).
- `--write_over`: Replace input files instead of writing to output directory.
- `--save-voc`: Save merged vocabulary JSON next to each translated file.
- `--chunk-size` / `--html-chunk-size`: Override default chunk lengths.
- `--verbose`: Enable debug logging via `loguru`.

#### Extra options for `abersetz engines`:
- `--family tr|dt|ll|hy`: Filter by engine family.
- `--configured-only`: Show only configured engines.

#### Extra options for `abersetz validate`:
- `--selectors tr/google,ll/default`: Limit checks to specific engines (comma-separated).
- `--target-lang es`: Set validation language (default: `es`).
- `--sample-text "Hello!"`: Use custom text for validation.

## Configuration

`abersetz` saves runtime configuration under the user config path from `platformdirs`. The config file includes:

- Global defaults (engine, languages, chunk sizes)
- Engine-specific settings (endpoints, retry policies, HTML behavior)
- Credential entries, supporting `{ "env": "ENV_NAME" }` or `{ "value": "actual-secret" }`

Example `config.toml`:

```toml
[defaults]
engine = "tr/google"
from_lang = "auto"
to_lang = "en"
chunk_size = 1200
html_chunk_size = 1800

[credentials.siliconflow]
name = "siliconflow"
env = "SILICONFLOW_API_KEY"

[engines.hysf]
chunk_size = 2400

[engines.hysf.credential]
name = "siliconflow"

[engines.hysf.options]
model = "tencent/Hunyuan-MT-7B"
base_url = "https://api.siliconflow.com/v1"
temperature = 0.3

[engines.ullm]
chunk_size = 2400

[engines.ullm.credential]
name = "siliconflow"

[engines.ullm.options.profiles.default]
base_url = "https://api.siliconflow.com/v1"
model = "tencent/Hunyuan-MT-7B"
temperature = 0.3
max_input_tokens = 32000

[engines.ullm.options.profiles.default.prolog]
```

Local engines (optional):

```toml
[engines.mthy]
name = "mthy"
chunk_size = 1200

[engines.mthy.options]
backend = "mlx" # or "gguf"
model_path = "/path/to/HY-MT1.5-7B-8bit"

[engines.gemma]
name = "gemma"
chunk_size = 1200

[engines.gemma.options]
backend = "gguf" # or "mlx"
model_path = "/path/to/translategemma-27b-it-Q8_0.gguf"
n_ctx = 4096
n_gpu_layers = -1
```

Use `abersetz config show` and `abersetz config path` to inspect the file.

## CLI Tools

- `abersetz`: Main CLI exposing `tr` (translate), `validate`, and `config` commands.
- `abtr`: Shorthand for translation (`abersetz tr`).

## Python API

```python
from abersetz import translate_path, TranslatorOptions

translate_path(
    path="docs",
    options=TranslatorOptions(to_lang="de", engine="tr/google"),
)
```

## Examples

The `examples/` folder includes ready-to-run demos:

- `poem_en.txt`: Source text.
- `poem_pl.txt`: Translated sample.
- `vocab.json`: Vocabulary generated during translation.
- `walkthrough.md`: Step-by-step CLI usage log.
- `validate_report.sh`: Captures validation summary for quick audits.

## Development Workflow

```bash
uv sync
python -m pytest --cov=. --cov-report=term-missing
ruff check src tests
ruff format src tests
```

## Testing Philosophy

- Unit tests cover every helper directly.
- Integration tests simulate the full pipeline with a stub engine.
- Network calls are mocked; CI never touches real APIs.

## License

MIT
