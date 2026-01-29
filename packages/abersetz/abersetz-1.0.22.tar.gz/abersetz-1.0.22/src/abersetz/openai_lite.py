"""Lightweight OpenAI API client using httpx - drop-in replacement for openai SDK."""
# this_file: src/abersetz/openai_lite.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class ChatCompletionMessage:
    """Represents a message in the chat completion response."""

    content: str | None
    role: str


@dataclass
class ChatCompletionChoice:
    """Represents a choice in the chat completion response."""

    message: ChatCompletionMessage
    index: int
    finish_reason: str | None = None


@dataclass
class ChatCompletionResponse:
    """Represents the full chat completion response."""

    choices: list[ChatCompletionChoice]
    id: str
    model: str
    usage: dict[str, int] | None = None


class ChatCompletions:
    """Chat completions API interface."""

    def __init__(self, client: OpenAI):
        self.client = client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def create(
        self, model: str, messages: list[dict[str, str]], temperature: float = 0.7, **kwargs: Any
    ) -> ChatCompletionResponse:
        """Create a chat completion.

        Args:
            model: The model to use for completion
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature
            **kwargs: Additional parameters passed to the API

        Returns:
            ChatCompletionResponse object compatible with OpenAI SDK
        """
        url = f"{self.client.base_url}/chat/completions"

        payload = {"model": model, "messages": messages, "temperature": temperature, **kwargs}

        headers = {
            "Authorization": f"Bearer {self.client.api_key}",
            "Content-Type": "application/json",
        }

        # Use httpx for the request
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        data = response.json()

        # Parse response into our dataclasses
        choices = []
        for choice_data in data.get("choices", []):
            message_data = choice_data.get("message", {})
            message = ChatCompletionMessage(
                content=message_data.get("content"), role=message_data.get("role", "assistant")
            )
            choice = ChatCompletionChoice(
                message=message,
                index=choice_data.get("index", 0),
                finish_reason=choice_data.get("finish_reason"),
            )
            choices.append(choice)

        return ChatCompletionResponse(
            choices=choices,
            id=data.get("id", ""),
            model=data.get("model", model),
            usage=data.get("usage"),
        )


class OpenAI:
    """Lightweight OpenAI client - drop-in replacement for the official SDK.

    This implementation provides the same API surface as the official OpenAI SDK
    but with minimal dependencies and fast import time. It only supports the
    chat completions API which is all that abersetz needs.
    """

    def __init__(self, api_key: str, base_url: str | None = None):
        """Initialize the OpenAI client.

        Args:
            api_key: The API key for authentication
            base_url: Optional base URL override (for compatible endpoints)
        """
        self.api_key = api_key
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.chat = Chat()
        self.chat.completions = ChatCompletions(self)


class Chat:
    """Chat API namespace with an optionally populated completions client."""

    completions: ChatCompletions | None

    def __init__(self) -> None:
        self.completions = None


__all__ = [
    "OpenAI",
    "ChatCompletionResponse",
    "ChatCompletionChoice",
    "ChatCompletionMessage",
    "Chat",
]
