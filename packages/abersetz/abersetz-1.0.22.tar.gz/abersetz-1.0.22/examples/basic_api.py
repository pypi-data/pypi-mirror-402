#!/usr/bin/env python3
# this_file: examples/basic_api.py

"""Basic example of using abersetz Python API."""

from collections.abc import Callable
from pathlib import Path

from abersetz import TranslatorOptions, translate_path

FALLBACK_DESCRIPTION = "No description provided."


def format_example_doc(func: Callable[..., object]) -> str:
    """Return a human-friendly description for an example function."""
    doc = func.__doc__
    if doc:
        return doc.strip()
    return FALLBACK_DESCRIPTION


# Example 1: Simple translation
def example_simple():
    """Translate a single file with default settings."""
    results = translate_path("poem_en.txt", TranslatorOptions(to_lang="es", engine="tr/google"))
    for result in results:
        print(f"Translated {result.source} -> {result.destination}")
        print(f"Used {result.chunks} chunks in {result.format.value} format")


# Example 2: Batch translation with output directory
def example_batch():
    """Translate multiple files to a specific directory."""
    results = translate_path(
        ".",  # Current directory
        TranslatorOptions(
            from_lang="en",
            to_lang="fr",
            engine="dt/google",
            include=("*.txt", "*.md"),
            xclude=("*_fr.txt", "*_fr.md"),
            output_dir=Path("translations/fr"),
            recurse=False,
        ),
    )
    print(f"Translated {len(results)} files")


# Example 3: Using LLM engine with voc
def example_llm_with_voc():
    """Use LLM translation with custom voc."""
    initial_vocab = {
        "abersetz": "abersetz (translation tool)",
        "chunk": "fragment",
        "pipeline": "pipeline",
    }

    results = translate_path(
        "technical_doc.md",
        TranslatorOptions(
            to_lang="de",
            engine="hy",  # or "ll/default"
            initial_voc=initial_vocab,
            save_voc=True,  # Save merged voc
            chunk_size=2000,
        ),
    )

    if results:
        print(f"Final voc: {results[0].voc}")


# Example 4: Dry run mode for testing
def example_dry_run():
    """Test translation without actually calling APIs."""
    results = translate_path(
        "test_files/",
        TranslatorOptions(
            to_lang="ja",
            engine="tr/bing",
            recurse=True,
            dry_run=True,  # Don't actually translate
        ),
    )
    for result in results:
        print(f"Would translate: {result.source}")


# Example 5: HTML file translation
def example_html():
    """Translate HTML files while preserving markup."""
    results = translate_path(
        "website/index.html",
        TranslatorOptions(
            from_lang="en",
            to_lang="pt",
            engine="dt/deepl",
            html_chunk_size=2500,  # Larger chunks for HTML
            write_over=False,  # Create new files
        ),
    )
    print(f"HTML translation complete: {results[0].destination}")


# Example 6: Custom configuration
def example_with_config():
    """Use custom configuration for translation."""
    from abersetz.config import load_config, save_config

    # Load and modify config
    config = load_config()
    config.defaults.to_lang = "es"
    config.defaults.chunk_size = 1500

    # Add custom engine config
    from abersetz.config import Credential, EngineConfig

    config.engines["custom_llm"] = EngineConfig(
        name="custom_llm",
        chunk_size=3000,
        credential=Credential(env="CUSTOM_API_KEY"),
        options={
            "base_url": "https://api.custom-llm.com/v1",
            "model": "translation-model-v1",
            "temperature": 0.3,
        },
    )
    save_config(config)

    # Use the custom configuration
    results = translate_path("document.txt", config=config)
    print(f"Translated with custom config: {results}")


if __name__ == "__main__":
    import sys

    examples = {
        "simple": example_simple,
        "batch": example_batch,
        "llm": example_llm_with_voc,
        "dry": example_dry_run,
        "html": example_html,
        "config": example_with_config,
    }

    if len(sys.argv) > 1 and sys.argv[1] in examples:
        examples[sys.argv[1]]()
    else:
        print(f"Usage: {sys.argv[0]} {{{','.join(examples.keys())}}}")
        print("\nAvailable examples:")
        for name, func in examples.items():
            description = format_example_doc(func)
            print(f"  {name}: {description}")
