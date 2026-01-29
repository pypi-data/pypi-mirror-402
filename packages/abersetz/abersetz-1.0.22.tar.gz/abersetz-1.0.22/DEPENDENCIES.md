# Dependencies

## Production Dependencies

### Translation Engines
- **translators** (>=5.9): Access to free translation APIs (Google, Bing, Baidu, etc.) through a single interface. Required for free translation support.
- **deep-translator** (>=1.11): Alternative translation library with additional providers including DeepL. Offers fallback options and file translation tools.
- **httpx** (>=0.25): Modern HTTP client with sync/async support. Replaces heavy SDKs with a lightweight implementation, cutting import time by 7.6 seconds.

### CLI and User Interface
- **fire** (>=0.5): Google's Python Fire library for automatic CLI generation. Minimal code, automatic help, intuitive commands.
- **rich** (>=13.9): Terminal formatting and progress indicators. Clean console output with tables, progress bars, and colors.
- **langcodes** (>=3.4): Language metadata based on CLDR. Powers `abersetz lang` without custom tables.
- **language-data** (>=1.4): Supplemental CLDR dataset required by `langcodes` for language names.

### Core Utilities
- **loguru** (>=0.7): Simple, structured logging with rotation and colored output.
- **platformdirs** (>=4.3): Cross-platform user directories. Ensures config files go in the right place.
- **tomli-w** (>=1.0): TOML serializer. Saves configuration data in `config.toml` without custom code.
- **tomli** (>=2.0, Python <3.11 only): Backport of the standard library TOML parser. Keeps config loading consistent across Python versions.
- **semantic-text-splitter** (>=0.7): Smart text chunking that respects semantic boundaries. Helps preserve context during translation.
- **tenacity** (>=8.4): Retry logic with exponential backoff. Handles API failures and rate limits.

### Optional Local Engines
- **mlx-lm**: Enables local MLX inference for HY-MT and TranslateGemma (`mthy/mlx`, `gemma/mlx`).
- **llama-cpp-python**: Enables local GGUF inference for HY-MT and TranslateGemma (`mthy/gguf`, `gemma/gguf`).

## Development Dependencies

### Testing
- **pytest** (>=8.3): Testing framework with fixtures and plugins.
- **pytest-cov** (>=6.0): Coverage reporting for pytest.

### Code Quality
- **ruff** (>=0.9): Fast linter and formatter. Replaces black, flake8, isort, and others.
- **mypy** (>=1.10): Static type checker. Catches type errors before runtime.

## Why These Packages?

1. **Multiple Translation Backends**: `translators` and `deep-translator` offer redundancy and access to different providers. Users can pick based on availability, quality, or cost.

2. **LLM Support**: The httpx-based client avoids heavy SDKs. Keeps LLM translation fast and lean.

3. **Developer Experience**: `fire` and `rich` make CLIs easy to build and debug. `loguru` simplifies logging setup.

4. **Reliability**: `tenacity` handles network issues. `semantic-text-splitter` keeps translation context intact.

5. **Cross-Platform**: `platformdirs` makes sure configs work everywhere—Windows, macOS, Linux.

6. **Code Quality**: Testing (91% coverage) and linting tools keep the codebase clean.

## Verification Log

- 2026-01-20 — Added `language-data` to keep `langcodes` language-name lookups working; optional local engine notes updated.
- 2025-09-21 11:03 UTC — /work reliability polish sweep (pytest, coverage, mypy, bandit) confirmed no dependency changes; improvements limited to tests and typing.
- 2025-09-21 08:46 UTC — /report QA sweep (pytest, coverage, mypy, bandit) confirmed dependency roster unchanged; no new packages.
- 2025-09-21 10:38 UTC — /work iteration adjusted tests only; dependency roster remains unchanged.
- 2025-09-21 10:29 UTC — /report QA sweep (pytest, coverage, mypy, bandit) confirmed dependency roster unchanged; no new packages.
- 2025-09-21 08:06 UTC — Post-/work QA sweep (pytest, coverage, mypy, bandit) introduced only tests; dependency roster unchanged.
- 2025-09-21 07:59 UTC — /report sweep reran full QA (pytest, coverage, mypy, bandit); dependency roster unchanged.
- 2025-09-21 05:38 UTC — Reviewed dependency roster during /report; no changes needed.
- 2025-09-21 05:50 UTC — Revalidated after quality guardrails sprint; no dependency changes.
- 2025-09-21 06:19 UTC — /report sweep confirmed dependency list remains accurate; no changes needed.
- 2025-09-21 06:27 UTC — Post-/work regression tests touched only test code; dependency roster unchanged.
- 2025-09-21 06:38 UTC — /report verification: reran full test/coverage/mypy/bandit sweep; dependency lineup unchanged.
- 2025-09-21 06:46 UTC — Configuration hardening tests added without altering dependencies; latest sweep confirms package set remains stable.
