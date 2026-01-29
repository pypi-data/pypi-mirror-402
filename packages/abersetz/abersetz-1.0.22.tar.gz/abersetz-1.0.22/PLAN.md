---
this_file: PLAN.md
---
# Abersetz Evolution Plan (Issue #200)

## Scope (One Sentence)
Deliver a responsive translation CLI that defaults to short engine selectors, validates every configured engine end-to-end, and ships with polished docs, examples, and tests that make abersetz easy to adopt and extend.

## Guiding Principles
- Preserve backward compatibility via aliases while promoting the short selector format (`tr/google`, `dt/deepl`, `ll/default`, etc.).
- Prefer existing, battle-tested packages (`translators`, `deep-translator`, httpx, rich) over custom reinventions.
- Ship every change with automated tests, documentation, and runnable examples.
- Prioritize fast feedback: run targeted pytest suites and smoke the CLI for every phase.

## Phase 4 – Auto-Configuration & Engine Research Enhancements
**Goal**: Broaden provider awareness and produce smarter defaults using the research in `external/` and recent API trends.
- Automate provider metadata extraction from `external/translators.txt`, `external/deep-translator.txt`, and current API research so discovery stays accurate without manual updates.
- Sync pricing/tier hints into setup output, highlighting free/community tiers and optional paid upgrades.
- Add structured hints for optional packages the user might need (for example `translators[google]`).
- [x] Allow users to opt into community/self-hosted engines such as LibreTranslate with a `--include-community` flag.
- Document every provider addition in `DEPENDENCIES.md` with justification referencing external sources.

## Phase 5 – Documentation, Examples, and Tests
**Goal**: Keep abersetz approachable with real-world material and strong guardrails.
- Update user-facing docs (`README.md`, `CLAUDE.md`, `CHANGELOG.md`, `docs/`) whenever selectors, validation workflows, or setup guidance changes.
- Expand `WORK.md` logging templates to capture validation runs and outcomes per session.
- Maintain at least three runnable examples in `examples/`: multi-file translation, validation summary report, and config diff before/after setup.
- Extend `docs/` (or README) with guidance on picking engines based on cost and availability, drawing on the provider research above.
- Ensure tests cover selector normalization, CLI output, validation command, setup integration, and documentation link checks.

## Maintenance Sprint – CLI Option Guardrails *(Completed)*
**Objective**: Backfill regression coverage for CLI option validation and propagation so user-facing flags behave predictably without introducing new functionality.

## Micro Sprint – README + CLI Option Defaults *(Completed)*
**Objective**: Keep documentation clean and ensure CLI option defaults resolve predictably.
- Remove assistant preamble/outro from `README.md`.
- Add `_build_options_from_cli` coverage for include defaults when omitted.
- Add `_build_options_from_cli` coverage for output dir resolution.
