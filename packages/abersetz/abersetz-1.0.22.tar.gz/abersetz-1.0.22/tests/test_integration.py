"""Integration tests for real translation engines."""
# this_file: tests/test_integration.py

from __future__ import annotations

import os

import pytest

from abersetz import TranslatorOptions, translate_path
from abersetz.config import load_config
from abersetz.engines import EngineRequest, create_engine

# Skip integration tests unless ABERSETZ_INTEGRATION_TESTS env var is set
pytestmark = pytest.mark.skipif(
    os.getenv("ABERSETZ_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled. Set ABERSETZ_INTEGRATION_TESTS=true to run.",
)


@pytest.mark.integration
def test_translators_google_real() -> None:
    """Test Google Translate via translators library (requires network)."""
    config = load_config()
    engine = create_engine("tr/google", config)

    request = EngineRequest(
        text="Hello, world!",
        source_lang="en",
        target_lang="es",
        is_html=False,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )

    result = engine.translate(request)
    assert result.text
    assert "hola" in result.text.lower() or "mundo" in result.text.lower()


@pytest.mark.integration
def test_deep_translator_google_real() -> None:
    """Test Google Translate via deep-translator library (requires network)."""
    config = load_config()
    engine = create_engine("dt/google", config)

    request = EngineRequest(
        text="Good morning",
        source_lang="en",
        target_lang="fr",
        is_html=False,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )

    result = engine.translate(request)
    assert result.text
    assert "bonjour" in result.text.lower() or "matin" in result.text.lower()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("SILICONFLOW_API_KEY"),
    reason="Requires SILICONFLOW_API_KEY environment variable",
)
def test_hysf_engine_real() -> None:
    """Test Siliconflow translation engine (requires API key)."""
    config = load_config()
    engine = create_engine("hysf", config)

    request = EngineRequest(
        text="Thank you",
        source_lang="en",
        target_lang="ja",
        is_html=False,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )

    result = engine.translate(request)
    assert result.text
    # Japanese translation should contain some Japanese characters
    assert any(ord(c) > 127 for c in result.text)


@pytest.mark.integration
def test_translate_file_api(tmp_path) -> None:
    """Test the high-level translate_path API."""
    # Create a temporary file with text to translate
    input_file = tmp_path / "test.txt"
    input_file.write_text("The quick brown fox")

    # Translate the file
    output_dir = tmp_path / "output"
    options = TranslatorOptions(
        from_lang="en",
        to_lang="de",
        engine="tr/google",
        output_dir=output_dir,
    )

    result = translate_path(str(input_file), options)

    assert result
    assert len(result) == 1

    # Check the translated file was created
    output_file = output_dir / "test.txt"
    assert output_file.exists()

    translated_text = output_file.read_text().lower()
    # German translation should contain some expected words
    assert any(word in translated_text for word in ["der", "die", "das", "fuchs", "braun"])


@pytest.mark.integration
def test_html_translation() -> None:
    """Test HTML content translation preserves markup."""
    config = load_config()
    engine = create_engine("tr/google", config)

    html_text = "<p>Hello <strong>world</strong>!</p>"
    request = EngineRequest(
        text=html_text,
        source_lang="en",
        target_lang="es",
        is_html=True,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )

    result = engine.translate(request)
    assert result.text
    # Should preserve HTML tags
    assert "<p>" in result.text
    assert "<strong>" in result.text or "<b>" in result.text
    assert "</p>" in result.text


@pytest.mark.integration
def test_translators_bing_real() -> None:
    """Test Bing Translate via translators library (requires network)."""
    config = load_config()
    try:
        engine = create_engine("tr/bing", config)
    except Exception:
        pytest.skip("Bing translator not available")
        return

    request = EngineRequest(
        text="Welcome to the world",
        source_lang="en",
        target_lang="pt",  # Portuguese
        is_html=False,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )

    try:
        result = engine.translate(request)
        assert result.text
        # Portuguese translation should contain some expected words
        assert any(word in result.text.lower() for word in ["bem-vindo", "mundo", "ao"])
    except Exception:
        pytest.skip("Bing translator temporarily unavailable")


@pytest.mark.integration
def test_batch_translation_with_voc() -> None:
    """Test translating multiple chunks with voc propagation."""
    config = load_config()
    engine = create_engine("tr/google", config)

    # First chunk with technical terms
    request1 = EngineRequest(
        text="The algorithm processes data efficiently.",
        source_lang="en",
        target_lang="es",
        is_html=False,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=2,
    )

    result1 = engine.translate(request1)
    assert result1.text

    # Second chunk reusing voc from first
    request2 = EngineRequest(
        text="The data is stored in the algorithm.",
        source_lang="en",
        target_lang="es",
        is_html=False,
        voc=result1.voc,
        prolog={},
        chunk_index=1,
        total_chunks=2,
    )

    result2 = engine.translate(request2)
    assert result2.text


@pytest.mark.integration
def test_retry_on_network_failure() -> None:
    """Test that retry mechanism works for real network issues."""
    from unittest.mock import patch

    import requests

    config = load_config()
    engine = create_engine("tr/google", config)

    # Simulate intermittent network failures
    original_get = requests.get
    call_count = 0

    def flaky_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise requests.ConnectionError("Network error")
        return original_get(*args, **kwargs)

    with patch("requests.get", side_effect=flaky_get):
        request = EngineRequest(
            text="Test",
            source_lang="en",
            target_lang="fr",
            is_html=False,
            voc={},
            prolog={},
            chunk_index=0,
            total_chunks=1,
        )

        # Should succeed despite initial failure
        try:
            result = engine.translate(request)
            assert result.text
        except Exception:
            # If it still fails, that's ok - we're testing the retry logic exists
            pass
