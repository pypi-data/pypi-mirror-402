---
layout: home
title: Home
nav_order: 1
description: "Abersetz is a minimalist file translator that reuses proven machine translation engines"
permalink: /
---

# abersetz
{: .fs-9 }

Minimalist file translator with pluggable engines  
{: .fs-6 .fw-300 }

[Get started](#getting-started){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }  
[View on GitHub](https://github.com/twardoch/abersetz){: .btn .fs-5 .mb-4 .mb-md-0 }  

---

## Why abersetz?

- **File-focused**: Translates documents, not just strings
- **Multiple engines**: Works with free and paid translation services
- **voc consistency**: LLM engines keep terminology consistent across chunks
- **Simple CLI**: Clean interface, minimal output
- **Python API**: Full programmatic access for automation

## Features

- **Multiple translation engines**
  - Free: Google, Bing via `translators` and `deep-translator`
  - LLM: OpenAI, Anthropic, SiliconFlow, and 20+ other providers
  - Custom endpoints for self-hosted models

- **Smart file handling**
  - Recursive directory translation
  - Pattern matching with include/exclude filters
  - Preserves HTML markup
  - Detects file formats automatically

- **Intelligent chunking**
  - Splits text semantically
  - Configurable chunk sizes per engine
  - Maintains context between chunks

- **voc management**
  - Propagates JSON-based terminology lists
  - Keeps long documents consistent
  - Optionally exports updated voc files

- **Engine validation**
  - `abersetz validate` performs basic smoke tests
  - Pulls latency and pricing data from internal catalog
  - Useful for CI checks and new user setup

## Getting Started

### Installation

```bash
pip install abersetz
```

### Quick Start

Run setup, validate engines, then translate a file:
```bash
abersetz setup
abersetz validate --target-lang es
abersetz tr es document.txt
```

Shorthand for translation:
```bash
abtr es document.txt
```

Translate a directory:
```bash
abersetz tr fr ./docs --output ./docs_fr
```

### Configuration

Abersetz saves config in your user directory:

```bash
abersetz config path  # Show config location
abersetz config show  # Display current settings
```

## Example Usage

### CLI Examples

```bash
# Translate with specific engine
abtr de file.txt --engine tr/google

# Translate markdown files only
abtr ja . --include "*.md" --output ./ja

# Dry run to preview files to be translated
abersetz tr zh-CN project/ --dry-run

# Validate specific engines
abersetz validate --selectors tr/google,ll/default

# Use LLM with terminology list
export SILICONFLOW_API_KEY="your-key"
abtr es technical.md --engine hy --save-voc
```

### Python API

```python
from abersetz import translate_path, TranslatorOptions

# Simple translation
results = translate_path(
    "document.txt",
    TranslatorOptions(
        to_lang="fr",
        engine="tr/google"
    )
)

# Batch translation with pattern filters
results = translate_path(
    "docs/",
    TranslatorOptions(
        to_lang="de",
        include=("*.md", "*.txt"),
        output_dir="docs_de/"
    )
)
```

## Documentation

- [Installation Guide](installation/)
- [CLI Reference](cli/)
- [Python API](api/)
- [Configuration](configuration/)
- [Translation Engines](engines/)
- [Examples](examples/)

## License

MIT License – see [LICENSE](https://github.com/twardoch/abersetz/blob/main