"""Translation engine adapters."""
# this_file: src/abersetz/engines.py

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from tenacity import retry, stop_after_attempt, wait_exponential

from .chunking import TextFormat
from .config import AbersetzConfig, EngineConfig, resolve_credential
from .engine_catalog import (
    HYSF_DEFAULT_MODEL,
    HYSF_DEFAULT_TEMPERATURE,
    normalize_selector,
    resolve_engine_reference,
)

# Use lightweight OpenAI client for fast imports
from .openai_lite import OpenAI


class EngineError(RuntimeError):
    """Raised when an engine cannot be constructed or invoked."""


MTHY_LANGUAGE_DATA = """
Chinese	zh	中文
English	en	英语
French	fr	法语
Portuguese	pt	葡萄牙语
Spanish	es	西班牙语
Japanese	ja	日语
Turkish	tr	土耳其语
Russian	ru	俄语
Arabic	ar	阿拉伯语
Korean	ko	韩语
Thai	th	泰语
Italian	it	意大利语
German	de	德语
Vietnamese	vi	越南语
Malay	ms	马来语
Indonesian	id	印尼语
Filipino	tl	菲律宾语
Hindi	hi	印地语
Traditional Chinese	zh-Hant	繁体中文
Polish	pl	波兰语
Czech	cs	捷克语
Dutch	nl	荷兰语
Khmer	km	高棉语
Burmese	my	缅甸语
Persian	fa	波斯语
Gujarati	gu	古吉拉特语
Urdu	ur	乌尔都语
Telugu	te	泰卢固语
Marathi	mr	马拉地语
Hebrew	he	希伯来语
Bengali	bn	孟加拉语
Tamil	ta	泰米尔语
Ukrainian	uk	乌克兰语
Tibetan	bo	藏语
Kazakh	kk	哈萨克语
Mongolian	mn	蒙古语
Uyghur	ug	维吾尔语
Cantonese	yue	粤语
"""

MTHY_PROMPT_NO_TERMS = """将以下文本翻译为{target_language}，注意只需要输出翻译后的结果，不要额外解释：
{source_text}
"""

MTHY_LANG_MAP: dict[str, str] = {}
for line in MTHY_LANGUAGE_DATA.strip().splitlines():
    english, code, chinese = line.split("\t")
    MTHY_LANG_MAP[english.lower()] = chinese
    MTHY_LANG_MAP[code.lower()] = chinese
    MTHY_LANG_MAP[chinese] = chinese


def _resolve_mthy_language(code: str) -> str:
    """Resolve HY-MT language code/name to Chinese label."""
    resolved = MTHY_LANG_MAP.get(code.lower())
    if resolved is None:
        raise EngineError(f"Unsupported HY-MT language: {code}")
    return resolved


@dataclass(slots=True)
class EngineRequest:
    """Payload passed to engines."""

    text: str
    source_lang: str
    target_lang: str
    is_html: bool
    voc: dict[str, str]
    prolog: dict[str, str]
    chunk_index: int
    total_chunks: int


@dataclass(slots=True)
class EngineResult:
    """Normalized engine output."""

    text: str
    voc: dict[str, str]


class Engine(Protocol):
    """Protocol implemented by engine adapters."""

    name: str
    chunk_size: int | None
    html_chunk_size: int | None

    def translate(self, request: EngineRequest) -> EngineResult:
        """Translate a chunk."""

    def chunk_size_for(self, fmt: TextFormat) -> int | None:
        """Return preferred chunk size for the given text format."""


class EngineBase:
    """Shared helpers for engines."""

    def __init__(
        self,
        name: str,
        chunk_size: int | None,
        html_chunk_size: int | None,
    ) -> None:
        self.name = name
        self.chunk_size = chunk_size
        self.html_chunk_size = html_chunk_size

    def chunk_size_for(self, fmt: TextFormat) -> int | None:
        if fmt is TextFormat.HTML and self.html_chunk_size:
            return self.html_chunk_size
        return self.chunk_size


class LocalMlxEngine(EngineBase):
    """Local MLX-backed engine for HY-MT and TranslateGemma."""

    def __init__(
        self,
        family: str,
        config: EngineConfig,
        model_path: str,
        *,
        max_tokens: int,
    ) -> None:
        super().__init__(config.name, config.chunk_size, config.html_chunk_size)
        self._family = family
        self._max_tokens = max_tokens
        path = Path(model_path)
        if not path.exists():
            raise EngineError(f"Model path does not exist: {model_path}")
        try:
            from mlx_lm import generate, load  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise EngineError("mlx-lm is required for MLX engines") from exc
        self._generate = generate
        self._model, self._tokenizer = load(model_path)

    def translate(self, request: EngineRequest) -> EngineResult:
        if self._family == "mthy":
            prompt = MTHY_PROMPT_NO_TERMS.format(
                target_language=_resolve_mthy_language(request.target_lang),
                source_text=request.text,
            )
            if hasattr(self._tokenizer, "apply_chat_template") and getattr(
                self._tokenizer, "chat_template", None
            ):
                messages = [{"role": "user", "content": prompt}]
                prompt = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            text = self._generate(
                self._model,
                self._tokenizer,
                prompt=prompt,
                max_tokens=self._max_tokens,
                verbose=False,
            )
            return EngineResult(text=text, voc=dict(request.voc))
        if self._family == "gemma":
            source_lang = request.source_lang if request.source_lang != "auto" else "en"
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "source_lang_code": source_lang,
                            "target_lang_code": request.target_lang,
                            "text": request.text,
                        }
                    ],
                }
            ]
            if not hasattr(self._tokenizer, "apply_chat_template"):
                raise EngineError("Gemma MLX tokenizer missing chat template support")
            prompt = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            text = self._generate(
                self._model,
                self._tokenizer,
                prompt=prompt,
                max_tokens=self._max_tokens,
                verbose=False,
            )
            return EngineResult(text=text.split("<end_of_turn>")[0].strip(), voc=dict(request.voc))
        raise EngineError(f"Unsupported MLX family '{self._family}'")


class LocalGgufEngine(EngineBase):
    """Local GGUF-backed engine for HY-MT and TranslateGemma."""

    def __init__(
        self,
        family: str,
        config: EngineConfig,
        model_path: str,
        *,
        max_tokens: int,
        temperature: float,
        n_gpu_layers: int,
        n_ctx: int,
    ) -> None:
        super().__init__(config.name, config.chunk_size, config.html_chunk_size)
        self._family = family
        self._max_tokens = max_tokens
        self._temperature = temperature
        path = Path(model_path)
        if not path.exists():
            raise EngineError(f"Model file does not exist: {model_path}")
        try:
            from llama_cpp import Llama  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise EngineError("llama-cpp-python is required for GGUF engines") from exc
        self._llm = Llama(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            verbose=False,
        )

    def translate(self, request: EngineRequest) -> EngineResult:
        if self._family == "mthy":
            prompt = MTHY_PROMPT_NO_TERMS.format(
                target_language=_resolve_mthy_language(request.target_lang),
                source_text=request.text,
            )
            messages = [{"role": "user", "content": prompt}]
        elif self._family == "gemma":
            source_lang = request.source_lang if request.source_lang != "auto" else "en"
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "source_lang_code": source_lang,
                            "target_lang_code": request.target_lang,
                            "text": request.text,
                        }
                    ],
                }
            ]
        else:
            raise EngineError(f"Unsupported GGUF family '{self._family}'")
        output = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        chunk_result = output["choices"][0]["message"]["content"]
        return EngineResult(text=chunk_result, voc=dict(request.voc))


class TranslatorsEngine(EngineBase):
    """Wrapper around the `translators` package with retry logic."""

    def __init__(self, provider: str, config: EngineConfig) -> None:
        super().__init__(config.name, config.chunk_size, config.html_chunk_size)
        self.provider = provider
        # Lazy import translators only when engine is created
        import translators  # type: ignore

        self._translators = translators

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10), reraise=True)
    def _translate_with_retry(
        self, text: str, is_html: bool, source_lang: str, target_lang: str
    ) -> str:
        """Internal method with retry logic for network failures."""
        if is_html:
            return self._translators.translate_html(
                text,
                translator=self.provider,
                from_language=source_lang,
                to_language=target_lang,
            )
        else:
            return self._translators.translate_text(
                text,
                translator=self.provider,
                from_language=source_lang,
                to_language=target_lang,
            )

    def translate(self, request: EngineRequest) -> EngineResult:
        text = self._translate_with_retry(
            request.text, request.is_html, request.source_lang, request.target_lang
        )
        return EngineResult(text=text, voc=dict(request.voc))


class DeepTranslatorEngine(EngineBase):
    """Adapter for `deep-translator` providers with retry logic."""

    PROVIDERS: Mapping[str, type] | None = None

    @classmethod
    def _get_providers(cls) -> Mapping[str, type]:
        """Lazy load deep-translator providers."""
        if cls.PROVIDERS is None:
            from deep_translator import (  # type: ignore
                DeeplTranslator,
                GoogleTranslator,
                LibreTranslator,
                LingueeTranslator,
                MicrosoftTranslator,
                MyMemoryTranslator,
                PapagoTranslator,
            )

            cls.PROVIDERS = {
                "google": GoogleTranslator,
                "deepl": DeeplTranslator,
                "microsoft": MicrosoftTranslator,
                "libre": LibreTranslator,
                "linguee": LingueeTranslator,
                "papago": PapagoTranslator,
                "my_memory": MyMemoryTranslator,
            }
        return cls.PROVIDERS

    def __init__(self, provider: str, config: EngineConfig) -> None:
        super().__init__(config.name, config.chunk_size, config.html_chunk_size)
        providers = self._get_providers()
        if provider not in providers:
            raise EngineError(f"Unsupported deep-translator provider: {provider}")
        self.provider = provider
        self._provider_class = providers[provider]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10), reraise=True)
    def _translate_with_retry(self, text: str, source_lang: str, target_lang: str) -> str:
        """Internal method with retry logic for network failures."""
        translator = self._provider_class(source=source_lang, target=target_lang)
        return translator.translate(text)

    def translate(self, request: EngineRequest) -> EngineResult:
        text = self._translate_with_retry(request.text, request.source_lang, request.target_lang)
        return EngineResult(text=text, voc=dict(request.voc))


class LlmEngine(EngineBase):
    """Shared logic for LLM backed engines."""

    OUTPUT_RE = re.compile(r"<output>(?P<body>.*?)</output>", re.DOTALL | re.IGNORECASE)
    VOCAB_RE = re.compile(r"<voc>(?P<body>.*?)</voc>", re.DOTALL | re.IGNORECASE)

    def __init__(
        self,
        config: EngineConfig,
        client: Any,
        *,
        model: str,
        temperature: float,
        static_prolog: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(config.name, config.chunk_size, config.html_chunk_size)
        self._client = client
        self._model = model
        self._temperature = temperature
        self._static_prolog = dict(static_prolog or {})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1), reraise=True)
    def _invoke(self, messages: list[dict[str, str]]) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
        )
        return response.choices[0].message.content or ""

    def translate(self, request: EngineRequest) -> EngineResult:
        voc = dict(self._static_prolog)
        voc.update(request.prolog)
        merged = dict(request.voc)
        messages = self._build_messages(request, voc, merged)
        raw = self._invoke(messages)
        text, new_vocab = self._parse_payload(raw)
        merged.update(new_vocab)
        return EngineResult(text=text, voc=merged)

    def _build_messages(
        self,
        request: EngineRequest,
        voc: Mapping[str, str],
        merged: Mapping[str, str],
    ) -> list[dict[str, str]]:
        vocab_payload: dict[str, str] = dict(voc)
        if merged:
            vocab_payload.setdefault("__current__", json.dumps(merged, ensure_ascii=False))
        prolog = json.dumps(vocab_payload, ensure_ascii=False) if vocab_payload else "{}"
        meta = {
            "chunk": request.chunk_index + 1,
            "total": request.total_chunks,
            "is_html": str(request.is_html).lower(),
        }
        instructions = (
            "Translate the <segment> into the target language. Respond with "
            '<output>...</output> and optionally <voc>{"new": "value"}</voc>.'
        )
        user_content = (
            f"<instructions>{instructions}</instructions>\n"
            f"<meta>{json.dumps(meta, ensure_ascii=False)}</meta>\n"
            f"<prolog>{prolog}</prolog>\n"
            f"<target>{request.target_lang}</target>\n"
            f"<source>{request.source_lang}</source>\n"
            f"<segment>{request.text}</segment>"
        )
        return [
            {
                "role": "system",
                "content": "You produce deterministic translations strictly in XML tags.",
            },
            {"role": "user", "content": user_content},
        ]

    def _parse_payload(self, payload: str) -> tuple[str, dict[str, str]]:
        text_match = self.OUTPUT_RE.search(payload)
        text = text_match.group("body").strip() if text_match else payload.strip()
        vocab_match = self.VOCAB_RE.search(payload)
        if not vocab_match:
            return text, {}
        try:
            vocab = json.loads(vocab_match.group("body"))
        except json.JSONDecodeError:
            vocab = {}
        if isinstance(vocab, dict):
            return text, {str(k): str(v) for k, v in vocab.items()}
        return text, {}


class HysfEngine(EngineBase):
    """Specialised HYSF engine with fixed prompt semantics."""

    MODEL = HYSF_DEFAULT_MODEL
    TEMPERATURE = HYSF_DEFAULT_TEMPERATURE

    def __init__(self, config: EngineConfig, client: Any) -> None:
        super().__init__(config.name, config.chunk_size, config.html_chunk_size)
        self._client = client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1), reraise=True)
    def _invoke(self, message: str) -> str:
        response = self._client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": message}],
            temperature=self.TEMPERATURE,
        )
        return response.choices[0].message.content or ""

    def translate(self, request: EngineRequest) -> EngineResult:
        language_name = self._language_name(request.target_lang)
        prompt = (
            f"Translate the following segment into {language_name}, without additional explanation.\n\n"
            f"{request.text}"
        )
        text = self._invoke(prompt).strip()
        return EngineResult(text=text, voc=dict(request.voc))

    @staticmethod
    def _language_name(code: str) -> str:
        try:
            from langcodes import get as get_language  # Lazy import

            return get_language(code).language_name("en") or code
        except Exception:  # pragma: no cover - unexpected lookup failure
            return code


def _make_openai_client(token: str, base_url: str | None) -> OpenAI:
    """Create an OpenAI client respecting optional base URL."""
    if base_url:
        return OpenAI(api_key=token, base_url=base_url)
    return OpenAI(api_key=token)


def _build_llm_engine(
    selector: str,
    config: AbersetzConfig,
    engine_cfg: EngineConfig,
    *,
    profile: Mapping[str, Any] | None,
    client: Any | None,
) -> Engine:
    options = dict(engine_cfg.options)
    settings = dict(profile or {})
    base_url = settings.get("base_url") or options.get("base_url")
    model = settings.get("model") or options.get("model")
    if not model:
        raise EngineError(f"No model configured for engine {selector}")
    temperature = float(settings.get("temperature", options.get("temperature", 0.9)))
    token = resolve_credential(config, engine_cfg.credential)
    if token is None:
        raise EngineError(f"Missing credential for engine {selector}")
    openai_client = client or _make_openai_client(token, base_url)
    static_prolog = settings.get("prolog") or options.get("prolog") or {}
    return LlmEngine(
        engine_cfg,
        openai_client,
        model=model,
        temperature=temperature,
        static_prolog=static_prolog,
    )


def _build_hysf_engine(
    selector: str,
    config: AbersetzConfig,
    engine_cfg: EngineConfig,
    *,
    client: Any | None,
) -> Engine:
    token = resolve_credential(config, engine_cfg.credential)
    if token is None:
        raise EngineError(f"Missing credential for engine {selector}")
    base_url = engine_cfg.options.get("base_url")
    openai_client = client or _make_openai_client(token, base_url)
    return HysfEngine(engine_cfg, openai_client)


def _translators_provider(variant: str | None, engine_cfg: EngineConfig) -> str:
    return variant or engine_cfg.options.get("provider", "google")


def _select_profile(engine_cfg: EngineConfig, variant: str | None) -> Mapping[str, Any] | None:
    profiles = engine_cfg.options.get("profiles", {})
    if not profiles:
        return None
    profile_name = variant or "default"
    if profile_name not in profiles:
        raise EngineError(f"Unknown profile '{profile_name}' for engine '{engine_cfg.name}'")
    return profiles[profile_name]


def create_engine(
    selector: str,
    config: AbersetzConfig,
    *,
    client: Any | None = None,
) -> Engine:
    """Factory that builds the requested engine supporting short aliases."""

    normalized = normalize_selector(selector) or selector
    base, variant = resolve_engine_reference(normalized)

    engine_cfg = config.engines.get(base)
    if engine_cfg is None:
        raise EngineError(f"No configuration found for engine '{base}'")
    if base == "translators":
        provider = _translators_provider(variant, engine_cfg)
        return TranslatorsEngine(provider, engine_cfg)
    if base == "deep-translator":
        provider = _translators_provider(variant, engine_cfg)
        return DeepTranslatorEngine(provider, engine_cfg)
    if base == "hysf":
        return _build_hysf_engine(normalized, config, engine_cfg, client=client)
    if base == "ullm":
        profile = _select_profile(engine_cfg, variant)
        return _build_llm_engine(normalized, config, engine_cfg, profile=profile, client=client)
    if base in {"mthy", "gemma"}:
        options = dict(engine_cfg.options)
        backend = (variant or options.get("backend") or "").strip().lower()
        if not backend:
            raise EngineError(f"No backend configured for engine {normalized}")
        models = options.get("models")
        model_map = models if isinstance(models, Mapping) else {}
        model_path = (
            options.get(f"{backend}_path")
            or options.get("model_path")
            or model_map.get(backend)
        )
        if not model_path:
            raise EngineError(f"No model path configured for engine {normalized}")
        max_tokens = int(options.get("max_tokens", 2048))
        temperature = float(options.get("temperature", 0.0))
        n_gpu_layers = int(options.get("n_gpu_layers", -1))
        n_ctx = int(options.get("n_ctx", 4096))
        if backend == "mlx":
            return LocalMlxEngine(base, engine_cfg, str(model_path), max_tokens=max_tokens)
        if backend == "gguf":
            return LocalGgufEngine(
                base,
                engine_cfg,
                str(model_path),
                max_tokens=max_tokens,
                temperature=temperature,
                n_gpu_layers=n_gpu_layers,
                n_ctx=n_ctx,
            )
        raise EngineError(f"Unsupported backend '{backend}' for engine '{normalized}'")
    raise EngineError(f"Unsupported engine '{base}'")


__all__ = [
    "Engine",
    "EngineError",
    "EngineRequest",
    "EngineResult",
    "create_engine",
]
