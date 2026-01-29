"""Tests for the lightweight OpenAI client shim."""
# this_file: tests/test_openai_lite.py

from __future__ import annotations

from typing import Any, get_type_hints

import httpx
import pytest

from abersetz.openai_lite import Chat, ChatCompletions, OpenAI


class _DummyResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code != 200:
            raise httpx.HTTPStatusError("boom", request=None, response=None)

    def json(self) -> dict[str, Any]:
        return self._payload


class _DummyClient:
    def __init__(self, response: _DummyResponse, calls: list[dict[str, Any]]) -> None:
        self._response = response
        self._calls = calls

    def __enter__(self) -> _DummyClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, *, json: dict[str, Any], headers: dict[str, str]) -> _DummyResponse:
        self._calls.append({"url": url, "json": json, "headers": headers})
        return self._response


def test_chat_completions_create_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    response = _DummyResponse(
        status_code=200,
        payload={
            "id": "resp-123",
            "model": "gpt-4o-mini",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "Translated"},
                }
            ],
        },
    )

    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **_: _DummyClient(response=response, calls=calls),
    )

    client = OpenAI(api_key="sk-test", base_url="https://api.example.com/")
    completions = client.chat.completions

    result = ChatCompletions.create.__wrapped__(
        completions,
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hola"}],
        temperature=0.2,
    )

    assert calls == [
        {
            "url": "https://api.example.com/chat/completions",
            "json": {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hola"}],
                "temperature": 0.2,
            },
            "headers": {
                "Authorization": "Bearer sk-test",
                "Content-Type": "application/json",
            },
        }
    ]
    assert result.id == "resp-123"
    assert result.model == "gpt-4o-mini"
    assert result.usage == {"prompt_tokens": 10, "completion_tokens": 5}
    assert len(result.choices) == 1
    assert result.choices[0].message.content == "Translated"
    assert result.choices[0].finish_reason == "stop"


def test_chat_completions_create_raises_for_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _DummyResponse(status_code=500, payload={})
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **_: _DummyClient(response=response, calls=[]),
    )

    client = OpenAI(api_key="secret")
    completions = client.chat.completions

    with pytest.raises(httpx.HTTPStatusError):
        ChatCompletions.create.__wrapped__(
            completions,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
        )


def test_openai_base_url_trims_trailing_slash() -> None:
    client = OpenAI(api_key="secret", base_url="https://api.custom/v1//")
    assert client.base_url == "https://api.custom/v1"
    assert isinstance(client.chat.completions, ChatCompletions)


def test_chat_declares_completions_attribute() -> None:
    hints = get_type_hints(Chat)
    assert hints.get("completions") == ChatCompletions | None


def test_openai_initializes_chat_completions() -> None:
    client = OpenAI(api_key="secret")
    assert isinstance(client.chat.completions, ChatCompletions)
