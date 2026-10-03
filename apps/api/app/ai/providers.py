"""Talking to a language model (Plan.md §9.8, provider abstraction).

The game only depends on `LLMProvider`. `OllamaProvider` talks to Ollama (a local model, or
an Ollama ":cloud" model); `FakeProvider` gives canned replies for tests and for running
without any AI. Gemini will be another implementation of the same interface.
"""

import json
from collections.abc import AsyncIterator, Sequence
from typing import Literal, Protocol

import httpx
from fastapi import Request
from pydantic import BaseModel, ValidationError


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMError(Exception):
    """The model couldn't be reached, timed out or replied with something unusable."""


class LLMProvider(Protocol):
    name: str

    def stream_chat(
        self, messages: Sequence[Message], *, max_tokens: int, temperature: float
    ) -> AsyncIterator[str]:
        """The reply, piece by piece as it's generated. Raises LLMError."""
        ...

    async def generate_json[T: BaseModel](self, messages: Sequence[Message], schema: type[T]) -> T:
        """A reply that matches `schema`. Raises LLMError."""
        ...

    async def aclose(self) -> None: ...


class OllamaProvider:
    """Ollama's chat API (https://github.com/ollama/ollama/blob/main/docs/api.md)."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float,
        *,
        think: bool | None = False,
        transport: httpx.AsyncBaseTransport | None = None,  # tests pass a mock
    ) -> None:
        self.name = f"ollama:{model}"
        self._model = model
        self._extra = {} if think is None else {"think": think}
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout, transport=transport)

    async def stream_chat(
        self, messages: Sequence[Message], *, max_tokens: int, temperature: float
    ) -> AsyncIterator[str]:
        body = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "stream": True,
            "options": {"num_predict": max_tokens, "temperature": temperature},
            **self._extra,
        }
        try:
            async with self._client.stream("POST", "/api/chat", json=body) as response:
                if response.status_code != 200:
                    detail = (await response.aread()).decode(errors="replace")[:200]
                    raise LLMError(f"Ollama answered {response.status_code}: {detail}")
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    if error := chunk.get("error"):
                        raise LLMError(f"Ollama: {error}")
                    if piece := chunk.get("message", {}).get("content"):
                        yield piece
                    if chunk.get("done"):
                        return
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama unreachable: {exc!r}") from exc

    async def generate_json[T: BaseModel](self, messages: Sequence[Message], schema: type[T]) -> T:
        body = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
            "format": schema.model_json_schema(),
            "options": {"temperature": 0},
            **self._extra,
        }
        try:
            response = await self._client.post("/api/chat", json=body)
            response.raise_for_status()
            return schema.model_validate_json(response.json()["message"]["content"])
        except (httpx.HTTPError, KeyError, ValidationError, ValueError) as exc:
            raise LLMError(f"Ollama JSON reply failed: {exc!r}") from exc

    async def aclose(self) -> None:
        await self._client.aclose()


class FakeProvider:
    """Canned replies, in order (then the last one again). For tests and AI-free runs."""

    name = "fake"

    def __init__(
        self,
        replies: Sequence[str] = (
            "*The dragon tilts its head and studies you, then nudges your hand.*\n"
            "💭 Friend. Probably.",
        ),
        *,
        fail: bool = False,
    ) -> None:
        self.replies = list(replies)
        self.fail = fail
        self.calls: list[list[Message]] = []

    async def stream_chat(
        self, messages: Sequence[Message], *, max_tokens: int, temperature: float
    ) -> AsyncIterator[str]:
        self.calls.append(list(messages))
        if self.fail:
            raise LLMError("fake failure")
        reply = self.replies[min(len(self.calls), len(self.replies)) - 1]
        for word in reply.split(" "):
            yield word + " "

    async def generate_json[T: BaseModel](self, messages: Sequence[Message], schema: type[T]) -> T:
        self.calls.append(list(messages))
        if self.fail:
            raise LLMError("fake failure")
        return schema.model_validate_json(self.replies[-1])

    async def aclose(self) -> None:
        return None


def get_llm(request: Request) -> LLMProvider:
    """The app's provider (created at startup from the settings)."""
    provider: LLMProvider = request.app.state.llm
    return provider
