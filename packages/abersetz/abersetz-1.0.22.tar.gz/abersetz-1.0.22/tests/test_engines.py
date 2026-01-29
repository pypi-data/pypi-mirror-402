"""Tests for translation engines."""
# this_file: tests/test_engines.py

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from langcodes import get as get_language

import abersetz.config as config_module
import abersetz.engines as engines_module
from abersetz.chunking import TextFormat
from abersetz.engines import EngineBase, EngineError, EngineRequest, create_engine


class DummyClient:
    """Simple stub mimicking OpenAI chat completions."""

    def __init__(self, payload: str):
        self.payload = payload
        self.calls: list[dict[str, object]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.payload)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


def test_translators_engine_invokes_library(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = config_module.load_config()
    captured: dict[str, object] = {}

    def fake_translate_text(
        text: str, translator: str, from_language: str, to_language: str, **_: object
    ) -> str:
        captured.update(
            {
                "text": text,
                "translator": translator,
                "from_language": from_language,
                "to_language": to_language,
            }
        )
        return "translated"

    fake_module = SimpleNamespace(
        translate_text=fake_translate_text,
        translate_html=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("translate_html should not be used")
        ),
    )
    monkeypatch.setitem(sys.modules, "translators", fake_module)
    engine = create_engine("tr/google", cfg)

    request = EngineRequest(
        text="hello",
        source_lang="en",
        target_lang="pl",
        is_html=False,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )
    result = engine.translate(request)
    assert result.text == "translated"
    assert captured["translator"] == "google"


def test_translators_engine_handles_html_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = config_module.load_config()
    captured: dict[str, object] = {}

    def fake_translate_html(
        text: str, translator: str, from_language: str, to_language: str, **_: object
    ) -> str:
        captured.update(
            {
                "text": text,
                "translator": translator,
                "from_language": from_language,
                "to_language": to_language,
            }
        )
        return "html-result"

    fake_module = SimpleNamespace(
        translate_text=lambda *_, **__: (_ for _ in ()).throw(
            AssertionError("translate_text should not be used for HTML")
        ),
        translate_html=fake_translate_html,
    )
    monkeypatch.setitem(sys.modules, "translators", fake_module)
    engine = create_engine("tr/google", cfg)

    request = EngineRequest(
        text="<p>Hello</p>",
        source_lang="en",
        target_lang="es",
        is_html=True,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )

    result = engine.translate(request)

    assert result.text == "html-result"
    assert captured["translator"] == "google"
    assert captured["text"] == "<p>Hello</p>"


def test_hysf_engine_uses_fixed_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = config_module.load_config()
    monkeypatch.setenv("SILICONFLOW_API_KEY", "env-key")
    payload = "cześć"
    client = DummyClient(payload)
    engine = create_engine("hysf", cfg, client=client)

    request = EngineRequest(
        text="hi",
        source_lang="en",
        target_lang="pl",
        is_html=False,
        voc={"existing": "value"},
        prolog={"ignored": "value"},
        chunk_index=0,
        total_chunks=1,
    )
    result = engine.translate(request)
    assert result.text == "cześć"
    # HYSF should not mutate vocabulary and should keep existing entries only
    assert result.voc == {"existing": "value"}
    assert client.calls  # ensure API invoked
    call = client.calls[0]
    expected_language = get_language("pl").language_name("en")
    expected_message = f"Translate the following segment into {expected_language}, without additional explanation.\n\nhi"
    assert call["model"] == "tencent/Hunyuan-MT-7B"
    assert call["temperature"] == 0.9
    assert call["messages"] == [{"role": "user", "content": expected_message}]


def test_engine_base_chunk_size_prefers_html_then_plain() -> None:
    engine = EngineBase(name="stub", chunk_size=800, html_chunk_size=1200)

    assert engine.chunk_size_for(TextFormat.HTML) == 1200
    assert engine.chunk_size_for(TextFormat.PLAIN) == 800

    fallback = EngineBase(name="fallback", chunk_size=None, html_chunk_size=None)
    assert fallback.chunk_size_for(TextFormat.HTML) is None


def test_ullm_engine_uses_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = config_module.load_config()
    profile = cfg.engines["ullm"].options["profiles"]["default"]
    profile["prolog"] = {"Term": "Translation"}
    config_module.save_config(cfg)
    monkeypatch.setenv("SILICONFLOW_API_KEY", "env-key")

    payload = '<output>done</output><voc>{"Term": "Done"}</voc>'
    client = DummyClient(payload)
    engine = create_engine("ullm/default", cfg, client=client)

    request = EngineRequest(
        text="Term",
        source_lang="en",
        target_lang="pl",
        is_html=False,
        voc={"Existing": "Istniejący"},
        prolog={},
        chunk_index=0,
        total_chunks=2,
    )
    result = engine.translate(request)
    assert result.text == "done"
    assert result.voc["Term"] == "Done"
    assert result.voc["Existing"] == "Istniejący"
    assert client.calls[0]["model"] == profile["model"]


def test_translators_engine_retry_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that TranslatorsEngine retries on network failures."""

    cfg = config_module.load_config()
    # Mock translators to fail twice then succeed
    call_count = 0

    def fake_translate_with_retry(
        text: str, translator: str, from_language: str, to_language: str, **_: object
    ) -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Network error")
        return "Translated after retries"

    fake_module = SimpleNamespace(
        translate_text=fake_translate_with_retry,
        translate_html=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("translate_html should not be used")
        ),
    )
    monkeypatch.setitem(sys.modules, "translators", fake_module)
    engine = create_engine("tr/google", cfg)

    request = EngineRequest(
        text="hello",
        source_lang="en",
        target_lang="pl",
        is_html=False,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )

    result = engine.translate(request)
    assert result.text == "Translated after retries"
    assert call_count == 3  # Two failures + one success


def test_create_engine_accepts_legacy_selector() -> None:
    cfg = config_module.load_config()
    engine = create_engine("translators/google", cfg)
    assert engine.name == "translators"


def test_deep_translator_engine_retry_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that DeepTranslatorEngine retries on network failures."""

    cfg = config_module.load_config()

    # Mock GoogleTranslator to fail twice then succeed
    call_count = 0

    class MockTranslator:
        def __init__(self, source: str, target: str):
            self.source = source
            self.target = target

        def translate(self, text: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "Translated after retries"

    # Patch the PROVIDERS dictionary directly
    from abersetz.engines import DeepTranslatorEngine

    # Force providers to be loaded first, then patch
    original_providers = dict(DeepTranslatorEngine._get_providers())
    DeepTranslatorEngine.PROVIDERS = {**original_providers, "google": MockTranslator}

    try:
        # Now create the engine after the mock is in place
        engine = create_engine("dt/google", cfg)

        request = EngineRequest(
            text="hello",
            source_lang="en",
            target_lang="pl",
            is_html=False,
            voc={},
            prolog={},
            chunk_index=0,
            total_chunks=1,
        )

        result = engine.translate(request)
        assert result.text == "Translated after retries"
        assert call_count == 3  # Two failures + one success
    finally:
        # Restore original PROVIDERS
        DeepTranslatorEngine.PROVIDERS = original_providers


def test_deep_translator_engine_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = config_module.load_config()

    with pytest.raises(EngineError, match="Unsupported deep-translator provider: unknown"):
        create_engine("dt/unknown", cfg)


def test_build_llm_engine_without_model_raises_engine_error() -> None:
    cfg = config_module.load_config()
    engine_cfg = cfg.engines["ullm"]
    profile = engine_cfg.options["profiles"]["default"]
    profile.pop("model", None)
    engine_cfg.options.pop("model", None)

    with pytest.raises(EngineError, match="No model configured"):
        create_engine("ullm/default", cfg)


def test_build_llm_engine_without_credential_raises_engine_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = config_module.load_config()
    engine_cfg = cfg.engines["ullm"]
    engine_cfg.options["profiles"]["default"].setdefault("model", "stub-model")
    engine_cfg.credential = config_module.Credential(name="missing")
    cfg.credentials.pop("missing", None)
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)

    with pytest.raises(EngineError, match="Missing credential"):
        create_engine("ullm/default", cfg)


def test_build_hysf_engine_without_credential_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = config_module.AbersetzConfig(
        credentials={},
        engines={},
    )
    engine_cfg = config_module.EngineConfig(
        name="hysf",
        credential=config_module.Credential(name="siliconflow"),
        options={},
    )
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)

    with pytest.raises(EngineError, match="Missing credential for engine hysf"):
        engines_module._build_hysf_engine("hysf", cfg, engine_cfg, client=None)


def test_select_profile_defaults_to_default_variant() -> None:
    cfg = config_module.load_config()
    engine_cfg = cfg.engines["ullm"]

    profile = engines_module._select_profile(engine_cfg, None)

    assert profile is engine_cfg.options["profiles"]["default"]


def test_select_profile_without_profiles_returns_none() -> None:
    engine_cfg = config_module.EngineConfig(name="ullm")

    assert engines_module._select_profile(engine_cfg, None) is None


def test_select_profile_unknown_variant_raises_engine_error() -> None:
    cfg = config_module.load_config()
    engine_cfg = cfg.engines["ullm"]

    with pytest.raises(EngineError, match="Unknown profile 'missing'"):
        engines_module._select_profile(engine_cfg, "missing")


def test_make_openai_client_respects_base_url() -> None:
    client = engines_module._make_openai_client("token", "https://example.com/api")

    assert client.base_url == "https://example.com/api"
    assert client.api_key == "token"


def test_make_openai_client_defaults_to_openai_url() -> None:
    client = engines_module._make_openai_client("token", None)

    assert client.base_url == "https://api.openai.com/v1"


def test_create_engine_with_unknown_configured_base_raises_engine_error() -> None:
    cfg = config_module.load_config()
    cfg.engines["custom"] = config_module.EngineConfig(name="custom")

    with pytest.raises(EngineError, match="Unsupported engine 'custom'"):
        create_engine("custom", cfg)


def _make_llm_engine() -> engines_module.LlmEngine:
    cfg = config_module.EngineConfig(name="llm-test")
    client = DummyClient(payload="")
    return engines_module.LlmEngine(
        cfg,
        client,
        model="stub-model",
        temperature=0.0,
        static_prolog={"Term": "Value"},
    )


def test_llm_engine_parse_payload_without_vocab() -> None:
    engine = _make_llm_engine()

    text, vocab = engine._parse_payload("<output>Hello</output>")

    assert text == "Hello"
    assert vocab == {}


def test_llm_engine_parse_payload_with_malformed_vocab() -> None:
    engine = _make_llm_engine()

    text, vocab = engine._parse_payload("<output>Hi</output><voc>{invalid}</voc>")

    assert text == "Hi"
    assert vocab == {}


def test_llm_engine_parse_payload_with_non_mapping_vocab() -> None:
    engine = _make_llm_engine()

    text, vocab = engine._parse_payload('<output>Hi</output><voc>["bad", "data"]</voc>')

    assert text == "Hi"
    assert vocab == {}


def test_create_engine_raises_when_config_missing_selector() -> None:
    cfg = config_module.load_config()
    cfg.engines.pop("translators", None)

    with pytest.raises(EngineError, match="No configuration found for engine 'translators'"):
        create_engine("tr/google", cfg)


def test_resolve_mthy_language_accepts_codes_and_names() -> None:
    assert engines_module._resolve_mthy_language("en") == "英语"
    assert engines_module._resolve_mthy_language("English") == "英语"
    assert engines_module._resolve_mthy_language("中文") == "中文"


def test_resolve_mthy_language_unknown_raises_engine_error() -> None:
    with pytest.raises(EngineError, match="Unsupported HY-MT language"):
        engines_module._resolve_mthy_language("xx")


def test_local_mthy_mlx_engine_translates_with_prompt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_dir = tmp_path / "mthy-mlx"
    model_dir.mkdir()
    cfg = config_module.AbersetzConfig(
        defaults=config_module.Defaults(engine="mthy"),
        engines={
            "mthy": config_module.EngineConfig(
                name="mthy",
                options={"backend": "mlx", "model_path": str(model_dir)},
            )
        },
    )
    tokenizer = SimpleNamespace(chat_template="template")
    captured: dict[str, object] = {}

    def fake_apply_chat_template(messages: list[dict[str, str]], **_: object) -> str:
        captured["messages"] = messages
        return "templated"

    def fake_generate(*_: object, **kwargs: object) -> str:
        captured["prompt"] = kwargs.get("prompt")
        return "translated"

    tokenizer.apply_chat_template = fake_apply_chat_template

    def fake_load(_: str) -> tuple[object, object]:
        return object(), tokenizer

    fake_module = SimpleNamespace(load=fake_load, generate=fake_generate)
    monkeypatch.setitem(sys.modules, "mlx_lm", fake_module)

    engine = create_engine("mthy", cfg)
    request = EngineRequest(
        text="Hello",
        source_lang="en",
        target_lang="en",
        is_html=False,
        voc={"existing": "value"},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )
    result = engine.translate(request)

    assert result.text == "translated"
    assert result.voc == {"existing": "value"}
    assert captured["prompt"] == "templated"
    message = captured["messages"][0]["content"]
    assert "将以下文本翻译为英语" in message


def test_local_gemma_gguf_engine_uses_structured_messages(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.write_text("stub", encoding="utf-8")
    cfg = config_module.AbersetzConfig(
        defaults=config_module.Defaults(engine="gemma/gguf"),
        engines={
            "gemma": config_module.EngineConfig(
                name="gemma",
                options={"backend": "gguf", "model_path": str(model_path)},
            )
        },
    )
    captured: dict[str, object] = {}

    class FakeLlama:
        def __init__(self, **kwargs: object) -> None:
            captured["init"] = kwargs

        def create_chat_completion(self, **kwargs: object) -> dict[str, object]:
            captured["call"] = kwargs
            return {"choices": [{"message": {"content": "result"}}]}

    monkeypatch.setitem(sys.modules, "llama_cpp", SimpleNamespace(Llama=FakeLlama))

    engine = create_engine("gemma/gguf", cfg)
    request = EngineRequest(
        text="Hello",
        source_lang="auto",
        target_lang="fr",
        is_html=False,
        voc={},
        prolog={},
        chunk_index=0,
        total_chunks=1,
    )
    result = engine.translate(request)

    assert result.text == "result"
    messages = captured["call"]["messages"]
    assert messages[0]["content"][0]["source_lang_code"] == "en"
    assert messages[0]["content"][0]["target_lang_code"] == "fr"
