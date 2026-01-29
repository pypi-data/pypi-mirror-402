---
layout: default
title: Python API
nav_order: 4
---

# Python API Reference
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

The abersetz Python API provides programmatic access to all translation functionality.

## Main Functions

### translate_path

Main function for translating files or directories.

```python
from abersetz import translate_path, TranslatorOptions

results = translate_path(
    path="document.txt",
    options=TranslatorOptions(to_lang="es"),
    config=None,  # Optional custom config
    client=None   # Optional HTTP client
)
```

**Parameters:**
- `path` (str | Path): File or directory to translate
- `options` (TranslatorOptions): Translation settings
- `config` (AbersetzConfig, optional): Custom configuration
- `client` (optional): HTTP client for API calls

**Returns:**
- List[TranslationResult]: Results for each translated file

## Core Classes

### TranslatorOptions

Configuration for translation operations.

```python
from abersetz import TranslatorOptions

options = TranslatorOptions(
    engine="tr/google",
    from_lang="auto",
    to_lang="en",
    recurse=True,
    write_over=False,
    output_dir=Path("output/"),
    save_voc=False,
    chunk_size=1200,
    html_chunk_size=1800,
    include=("*.txt", "*.md"),
    xclude=("*test*",),
    dry_run=False,
    prolog={"role": "translator"},
    initial_voc={"term": "translation"}
)
```

**Attributes:**
- `engine` (str): Translation engine name
- `from_lang` (str): Source language code
- `to_lang` (str): Target language code
- `recurse` (bool): Process subdirectories
- `write_over` (bool): Replace original files
- `output_dir` (Path): Output directory path
- `save_voc` (bool): Save vocabulary JSON
- `chunk_size` (int): Characters per text chunk
- `html_chunk_size` (int): Characters per HTML chunk
- `include` (tuple): File patterns to include
- `xclude` (tuple): File patterns to exclude
- `dry_run` (bool): Preview without translating
- `prolog` (dict): Initial context for LLMs
- `initial_voc` (dict): Starting vocabulary

### TranslationResult

Result information for a translated file.

```python
from abersetz import TranslationResult

result = TranslationResult(
    source=Path("input.txt"),
    destination=Path("output.txt"),
    chunks=5,
    voc={"term": "translation"},
    format=TextFormat.PLAIN
)
```

**Attributes:**
- `source` (Path): Source file path
- `destination` (Path): Output file path
- `chunks` (int): Number of chunks processed
- `voc` (dict): Final vocabulary (LLM engines)
- `format` (TextFormat): Detected format (PLAIN, HTML, MARKDOWN)

### PipelineError

Exception raised when translation fails.

```python
from abersetz import PipelineError

try:
    results = translate_path("missing.txt")
except PipelineError as e:
    print(f"Translation failed: {e}")
```

## Configuration Management

### Loading Configuration

```python
from abersetz.config import load_config

config = load_config()
print(config.defaults.engine)
print(config.defaults.to_lang)
```

### Saving Configuration

```python
from abersetz.config import save_config, AbersetzConfig, Defaults

config = AbersetzConfig(
    defaults=Defaults(
        engine="tr/google",
        to_lang="es",
        chunk_size=1500
    )
)

save_config(config)
```

### Custom Engine Configuration

```python
from abersetz.config import EngineConfig, Credential

config.engines["custom"] = EngineConfig(
    name="custom",
    chunk_size=2000,
    credential=Credential(env="CUSTOM_API_KEY"),
    options={
        "base_url": "https://api.custom.com/v1",
        "model": "translation-v1"
    }
)
```

## Engine Management

### Creating Engines

```python
from abersetz.engines import create_engine
from abersetz.config import load_config

config = load_config()
engine = create_engine("tr/google", config)
```

### Using Engines Directly

```python
from abersetz.engines import EngineRequest

request = EngineRequest(
    text="Hello world",
    source_lang="en",
    target_lang="es",
    is_html=False,
    voc={},
    prolog={},
    chunk_index=0,
    total_chunks=1
)

result = engine.translate(request)
print(result.text)  # "Hola mundo"
```

## Text Processing

### Format Detection

```python
from abersetz.chunking import detect_format, TextFormat

text = "<h1>Title</h1><p>Content</p>"
format = detect_format(text)
# Returns TextFormat.HTML
```

### Text Chunking

```python
from abersetz.chunking import chunk_text, TextFormat

chunks = chunk_text(
    text="Long document...",
    max_size=1000,
    format=TextFormat.MARKDOWN
)
```

## Complete Examples

### Simple Translation

```python
from abersetz import translate_path, TranslatorOptions

# Translate a single file
results = translate_path(
    "document.txt",
    TranslatorOptions(
        to_lang="fr",
        engine="tr/google"
    )
)

for result in results:
    print(f"Translated: {result.source} -> {result.destination}")
    print(f"Chunks: {result.chunks}")
```

### Batch Processing

```python
from pathlib import Path
from abersetz import translate_path, TranslatorOptions

def batch_translate(source_dir, languages, engine="tr/google"):
    """Translate to multiple languages."""
    results = {}

    for lang in languages:
        print(f"Translating to {lang}...")
        lang_results = translate_path(
            source_dir,
            TranslatorOptions(
                to_lang=lang,
                engine=engine,
                output_dir=Path(f"output_{lang}"),
                recurse=True
            )
        )
        results[lang] = lang_results

    return results

# Usage
results = batch_translate("docs/", ["es", "fr", "de"])
```

### Custom Workflow

```python
from abersetz import translate_path, TranslatorOptions
from abersetz.config import load_config, save_config
import json

class TranslationWorkflow:
    def __init__(self):
        self.config = load_config()
        self.voc = {}

    def translate_with_voc(self, files, to_lang):
        """Maintain vocabulary across files."""
        all_results = []

        for file in files:
            results = translate_path(
                file,
                TranslatorOptions(
                    to_lang=to_lang,
                    engine="ll/default",
                    initial_voc=self.voc,
                    save_voc=True
                ),
                config=self.config
            )

            if results:
                # Update vocabulary
                self.voc.update(results[0].voc)
                all_results.extend(results)

        # Save final vocabulary
        with open(f"voc_{to_lang}.json", "w") as f:
            json.dump(self.voc, f, indent=2)

        return all_results

# Usage
workflow = TranslationWorkflow()
results = workflow.translate_with_voc(
    ["doc1.md", "doc2.md", "doc3.md"],
    "es"
)
```

### Error Handling

```python
from abersetz import translate_path, TranslatorOptions, PipelineError
import logging

def safe_translate(path, **options):
    """Translate with comprehensive error handling."""
    try:
        results = translate_path(
            path,
            TranslatorOptions(**options)
        )
        return results

    except PipelineError as e:
        logging.error(f"Translation pipeline error: {e}")
        return None

    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        return None

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

# Usage with retry
import time

for attempt in range(3):
    results = safe_translate("document.txt", to_lang="es")
    if results:
        break
    time.sleep(2 ** attempt)  # Exponential backoff
```

### Async Translation

```python
import asyncio
from abersetz import translate_path, TranslatorOptions

async def translate_async(path, to_lang):
    """Async wrapper for translation."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        translate_path,
        path,
        TranslatorOptions(to_lang=to_lang)
    )

async def translate_multiple(files, to_lang):
    """Translate multiple files concurrently."""
    tasks = [translate_async(f, to_lang) for f in files]
    return await asyncio.gather(*tasks)

# Usage
files = ["doc1.txt", "doc2.txt", "doc3.txt"]
results = asyncio.run(translate_multiple(files, "es"))
```

## Advanced Topics

### Custom Engines

```python
from abersetz.engines import EngineBase, EngineRequest, EngineResult

class CustomEngine(EngineBase):
    """Custom translation engine implementation."""

    def __init__(self, config):
        super().__init__("custom", 1000, 1500)
        self.config = config

    def translate(self, request: EngineRequest) -> EngineResult:
        # Your translation logic here
        translated = self.call_api(request.text)
        return EngineResult(
            text=translated,
            voc={}
        )
```

### Vocabulary Management

```python
from typing import Dict
import json

class VocabularyManager:
    """Manage translation vocabularies."""

    def __init__(self):
        self.vocabularies: Dict[str, Dict[str, str]] = {}

    def load(self, path: str, lang_pair: str):
        with open(path) as f:
            self.vocabularies[lang_pair] = json.load(f)

    def merge(self, *lang_pairs: str) -> Dict[str, str]:
        merged = {}
        for pair in lang_pairs:
            if pair in self.vocabularies:
                merged.update(self.vocabularies[pair])
        return merged

    def save(self, voc: Dict[str, str], path: str):
        with open(path, "w") as f:
            json.dump(voc, f, indent=2, ensure_ascii=False)
```

## See Also

- [CLI Reference](cli/)
- [Configuration Guide](configuration/)
- [Examples](examples/)