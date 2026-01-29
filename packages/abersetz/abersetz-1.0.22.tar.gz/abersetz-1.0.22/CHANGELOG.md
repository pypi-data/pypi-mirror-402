---
this_file: CHANGELOG.md
---
# Changelog

All notable changes to abersetz will be documented in this file.

## [Unreleased]

### Added
- Added optional local MLX/GGUF engines for HY-MT and TranslateGemma via `mthy` and `gemma` selectors.
- Added `language-data` dependency to keep `langcodes` language-name lookups working in HYSF prompts.
- Added CLI regression tests covering target-language guardrails, JSON prolog/voc ingestion, and option propagation.
- Added CLI regression tests for include defaults and output directory resolution.
- Added `--include-community` flag to `abersetz setup` for opting into community/self-hosted engines.

### Changed
- Removed assistant preamble/outro text from `README.md`.

## [1.0.19] - 2025-09-21

### Highlights
- Short engine selectors are the default across the CLI, configuration, and engine catalog while keeping legacy aliases working transparently.
- New `abersetz validate` command reuses the engine pipeline to smoke-test configured selectors and slots into the setup wizard’s post-install checks.
- Refreshed docs, richer examples, and a 98% coverage regression suite backed by clean mypy and bandit runs.

### Added
- Introduced `src/abersetz/validation.py` and the `abersetz validate` CLI command for quick engine verification with rich table output.
- Extended the setup wizard to persist validation results, surface pricing hints, and auto-map discovered API keys to their short selectors.
- Added validation/reporting utilities such as `examples/validate_report.sh` and `translation_report.json` to demonstrate end-to-end health checks.
- Delivered new regression suites covering engine catalog discovery, setup wizard flows, validation pipelines, CLI Fire entrypoints, and advanced examples.

### Changed
- Normalised selector handling to prefer `tr/*`, `dt/*`, `ll/*`, and `hy` forms with automatic migration of legacy `translators/*` and `deep-translator/*` values.
- Updated `_build_options_from_cli` to accept `Path` objects, enforce target-language requirements, and hydrate JSON `prolog`/`voc` inputs consistently.
- Refined engine catalog rendering, configuration helpers, and setup wizard messaging to highlight credential needs and community/paid tiers.

### Fixed
- Resolved pipeline chunk-size fallbacks so engines supply sizes when configuration defaults collapse to zero, covering both plain text and HTML flows.
- Hardened setup wizard endpoint probing and validation logging to survive missing keys and transient HTTP failures.
- Eliminated the final mypy diagnostics by tightening optional typing around CLI outputs and external provider dumps.

### Documentation
- Refreshed `README.md`, reference docs, and example notebooks to describe short selectors, validation usage, and setup wizard improvements.
- Updated agent notebooks (`CLAUDE.md`, `GEMINI.md`, `LLXPRT.md`, `QWEN.md`) and examples to reflect the new validation workflow and selector syntax.

### Testing & Quality
- Test suite: `python -m pytest -xvs` reports 180 passed / 8 skipped with 98% coverage.
- Static analysis: `uvx mypy .` is clean (annotation-unchecked warning only); `uvx bandit -r .` reports Low-severity issues confined to intentional test `assert`s and backup fallbacks.
- Routine cleanup removes transient caches (`.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.benchmarks`, `.coverage`) after every verification sweep.

## [0.1.0] - 2025-01-20

### Added
- Initial release of abersetz - minimalist file translator
- Core translation pipeline with locate → chunk → translate → merge workflow
- Support for multiple translation engines:
  - translators library (Google, Bing, etc.)
  - deep-translator library (DeepL, Google Translate, etc.)
  - Custom hysf engine using Siliconflow API
  - Custom ullm engine for LLM-based translation with voc management
- Automatic file discovery with recursive globbing and include/xclude filters
- HTML vs plain-text detection for markup preservation
- Semantic chunking using semantic-text-splitter for better context boundaries
- voc-aware translation pipeline with JSON voc propagation
- Configuration management using platformdirs for portable settings
- Environment variable support for API credentials
- Fire-based CLI with rich console output
- Comprehensive test suite with 91% code coverage
- Example files demonstrating usage

### Fixed
- Fixed pyproject.toml configuration for modern uv/hatch compatibility
- Updated dependency group configuration to use standard [dependency-groups]
- Fixed type annotations to use modern Python union syntax (|)

## [0.1.1] - 2025-01-21

### Changed
- Renamed CLI main command from `translate` to `tr` for brevity
- Added `abtr` console script as direct shorthand for `abersetz tr`
- Improved CLI help output by instantiating the Fire class correctly
- Reduced logging and rich output to minimum for cleaner interface
- Simplified CLI output to just show destination files

### Added
- Version command (`abersetz version`) to display tool version
- Language code validation with silent handling of non-standard codes

### Fixed
- Fixed Fire CLI to properly expose available commands in help output
- Updated test suite to match renamed CLI command
- Fixed deep-translator retry test by properly mocking the provider

### Improved
- Better error handling for malformed config files with automatic backup
- Added retry mechanisms with tenacity for all translation engines
- Created comprehensive integration tests with skip markers for CI

### Technical Details
- Python 3.10+ support
- Semantic chunking with configurable sizes per engine
- Offline-friendly dry-run mode for testing
- Optional voc sidecar files with --save-voc flag
- Retry logic with tenacity for robust API calls
