Sure. Let's go step-by-step.

---

## @PLAN.md

```markdown
# Project Plan: `abersetz`

## Overview
`abersetz` is a Python package and CLI tool for translating text files using various translation engines. It supports both single and multiple file translation, with configurable chunking, language detection, and output handling.

## Key Features
- File discovery with optional recursion (`--recurse`)
- Chunking of files for translation
- Support for multiple translation engines:
  - External packages: `translators`, `deep-translator`
  - Custom engines:
    - `hysf`: Uses OpenAI client to call SiliconFlow API with `tencent/Hunyuan-MT-7B`
    - `ullm`: Configurable LLM translation engine with custom vocabulary support
- Language detection and specification (`--from`, `--to`)
- HTML content detection
- Vocabulary tracking and persistence across chunks (`<voc>` tag)
- Output control:
  - Save to new directory
  - Overwrite original files (`--write_over`)
  - Optional vocabulary export (`--save_voc`)

## Architecture
1. **File Discovery Module**
   - Accept file paths or glob patterns
   - Optional recursive scanning (`--recurse`)
2. **Text Splitting Module**
   - Use `text-splitter` or `tokenizers`/`tiktoken` for intelligent chunking
   - Configurable chunk size per engine
3. **Translation Engine Interface**
   - Unified interface for calling translation backends
   - Implement wrappers for:
     - `translators`
     - `deep-translator`
     - Custom `hysf` engine (OpenAI + tenacity)
     - Custom `ullm` engine (OpenAI + tenacity + configurable endpoints)
4. **Language Handling**
   - Use `langcodes` for standardizing language codes
   - Auto-detect source language unless specified
5. **HTML Detection**
   - Detect HTML content using simple heuristics or `ftfy`
6. **Vocabulary Management**
   - Extract and merge `<voc>` from LLM responses
   - Maintain state across chunks
   - Optionally save vocabulary to JSON
7. **Output Module**
   - Write translated files to a new directory or overwrite originals
8. **CLI Tool**
   - Use `fire` for CLI generation
   - Mimic structure and logic of `cerebrate-file`
   - Support all engine types and flags

## Dependencies
- `fire`
- `platformdirs`
- `langcodes`
- `ftfy`
- `translators`
- `deep-translator`
- `openai`
- `tenacity`
- `text-splitter` or `tokenizers`/`tiktoken`

## Configuration Storage
- Store API keys and engine-specific settings in user config directory using `platformdirs`
- Support both environment variable names and literal values

## File Structure
```
abersetz/
├── __init__.py
├── cli.py
├── core.py
├── engines/
│   ├── __init__.py
│   ├── base.py
│   ├── translators_engine.py
│   ├── deep_translator_engine.py
│   ├── hysf_engine.py
│   └── ullm_engine.py
├── splitter.py
├── voc.py
├── config.py
└── utils.py
```

## Examples Folder
- Real-world translation examples
- Various file types (txt, html, md)
- Demonstrations of vocabulary handling
```

---

## @TODO.md

```markdown
# Implementation TODO

- [ ] Create project structure and directories
- [ ] Set up `platformdirs` for config storage
- [ ] Implement config loading/saving for API keys and chunk sizes
- [ ] Add language code validation with `langcodes`
- [ ] Implement file discovery with optional `--recurse`
- [ ] Add HTML detection logic
- [ ] Integrate `text-splitter` or token-based chunking
- [ ] Define base translation engine interface
- [ ] Wrap `translators` package into engine class
- [ ] Wrap `deep-translator` package into engine class
- [ ] Implement `hysf` engine using OpenAI and tenacity
- [ ] Implement `ullm` engine with configurable API endpoints
- [ ] Add vocabulary (`<voc>`) parsing and merging logic
- [ ] Implement file output logic (new folder or overwrite)
- [ ] Build CLI with `fire`, mimicking `cerebrate-file`
- [ ] Add support for `--from`, `--to`, `--write_over`, `--save_voc`
- [ ] Write real-world examples in `examples/` folder
- [ ] Test all engines with sample files
- [ ] Verify vocabulary consistency across chunks
- [ ] Refine chunking and error handling
- [ ] Add version info and basic help output
- [ ] Document usage in updated `README.md`
```

---

## @README.md

```markdown
# abersetz

A minimal file translation tool and Python package. Translate text in single or multiple files using a variety of translation engines, including free online services and custom LLM-based backends.

## Features

- Translate entire files (not just raw text)
- Recursive file scanning (`--recurse`)
- Configurable chunk-based translation for large texts
- Built-in language detection or manual specification (`--from`, `--to`)
- HTML content auto-detection
- Vocabulary consistency for LLM engines (`<voc>` tag handling)
- Save translations to new folder or overwrite originals (`--write_over`)
- Optional vocabulary export (`--save_voc`)

## Supported Engines

### External
- `bing`, `google`, `yandex` etc. via [`translators`](https://pypi.org/project/translators/)
- Various services via [`deep-translator`](https://pypi.org/project/deep-translator/)

### Custom
- `hysf`: Calls SiliconFlow API using `tencent/Hunyuan-MT-7B` model via OpenAI client
- `ullm`: Universal LLM engine with configurable endpoints, models, and vocabulary support

## Installation

```bash
pip install abersetz
```

## Usage

```bash
# Translate a file or