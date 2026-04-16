"""Tests for the web_search module in the chain_reaction package."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.runnables import Runnable, RunnableLambda
from pydantic import BaseModel, Field
from pytest_check import check

from chain_reaction.web_search import (
    RelevanceVerdict,
    SearchResult,
    _fetch_and_extract,
    _filter_relevant_urls,
    _is_worth_fetching,
)

# region Fakes


class FakeJudgeChatModel(GenericFakeChatModel):
    """Fake chat model that returns scripted structured verdicts keyed by URL.

    The ``url_verdicts`` mapping associates a URL substring with either a bool
    verdict or a ``BaseException`` subclass to raise when that URL appears in
    the prompt. ``with_structured_output`` returns a small ``Runnable`` that
    inspects the final message content, looks up the matching entry, and
    either produces a schema instance or raises.

    Attributes:
        url_verdicts (dict[str, bool | type[BaseException]]): Map of URL
            substring to the verdict (or exception type) to produce.
    """

    url_verdicts: dict[str, bool | type[BaseException]] = Field(default_factory=dict)

    def with_structured_output(
        self,
        schema: dict[str, Any] | type,
        *,
        include_raw: bool = False,  # noqa: ARG002
        **_kwargs: Any,
    ) -> Runnable:
        """Return a runnable that produces ``schema`` instances from scripted verdicts."""
        if not isinstance(schema, type):
            msg_err = f"FakeJudgeChatModel only supports class schemas, got {schema!r}"
            raise TypeError(msg_err)
        return RunnableLambda(lambda messages: _apply_verdict(self.url_verdicts, schema, messages))


def _apply_verdict(
    verdicts: dict[str, bool | type[BaseException]],
    schema: type,
    messages: list[Any],
) -> BaseModel:
    """Resolve the scripted verdict for the URL found in ``messages``."""
    msg = messages[-1]
    content = msg["content"] if isinstance(msg, dict) else msg.content
    for url, verdict in verdicts.items():
        if url in content:
            if isinstance(verdict, type) and issubclass(verdict, BaseException):
                raise verdict(f"scripted failure for {url}")
            return schema(is_relevant=verdict)
    msg_err = f"no scripted verdict matched message content: {content!r}"
    raise AssertionError(msg_err)


# endregion

# region _fetch_and_extract


def test_fetch_and_extract_returns_markdown_for_valid_html() -> None:
    """A 200 response with extractable HTML should yield a SearchResult with markdown content."""
    # Arrange
    url = "https://example.com/python-guide"
    html = (
        "<html><body><article><h1>Python Guide</h1>"
        "<p>Python is a versatile programming language used for web development, "
        "data science, and machine learning. It has a simple syntax that makes "
        "it beginner-friendly.</p>"
        "<p>Key features include dynamic typing, automatic memory management, "
        "and a large standard library.</p></article></body></html>"
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, html=html)

    async def run() -> SearchResult | None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await _fetch_and_extract(client, url, asyncio.Semaphore(1))

    # Act
    result = asyncio.run(run())

    # Assert
    assert result is not None
    with check:
        assert result.url == url
    with check:
        assert "Python Guide" in result.content
    with check:
        assert "dynamic typing" in result.content


def test_fetch_and_extract_returns_none_for_non_200_response() -> None:
    """A non-200 response should cause the fetch to return None."""
    # Arrange
    url = "https://example.com/missing"

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    async def run() -> SearchResult | None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await _fetch_and_extract(client, url, asyncio.Semaphore(1))

    # Act
    result = asyncio.run(run())

    # Assert
    assert result is None


def test_fetch_and_extract_returns_none_on_transport_error() -> None:
    """Transport-level HTTP errors should be swallowed and return None."""
    # Arrange
    url = "https://unreachable.example/"

    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    async def run() -> SearchResult | None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await _fetch_and_extract(client, url, asyncio.Semaphore(1))

    # Act
    result = asyncio.run(run())

    # Assert
    assert result is None


def test_fetch_and_extract_returns_none_when_content_is_not_extractable() -> None:
    """A 200 response with no extractable content should return None."""
    # Arrange
    url = "https://example.com/empty"

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, html="<html><body></body></html>")

    async def run() -> SearchResult | None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await _fetch_and_extract(client, url, asyncio.Semaphore(1))

    # Act
    result = asyncio.run(run())

    # Assert
    assert result is None


# endregion

# region Relevance gate


@pytest.mark.parametrize("verdict", [True, False])
def test_is_worth_fetching_returns_model_verdict(verdict: bool) -> None:  # noqa: FBT001
    """The relevance gate should return the bool produced by the chat model."""
    # Arrange
    url = "https://example.com/article"
    chat_model = FakeJudgeChatModel(
        messages=iter([]),
        url_verdicts={url: verdict},
    )
    judge = chat_model.with_structured_output(RelevanceVerdict)

    async def run() -> bool:
        return await _is_worth_fetching(
            judge,
            query="python async patterns",
            url=url,
            snippet="an article about asyncio",
            semaphore=asyncio.Semaphore(1),
        )

    # Act
    result = asyncio.run(run())

    # Assert
    assert result is verdict


def test_filter_relevant_urls_keeps_only_passing_urls() -> None:
    """_filter_relevant_urls should return only URLs the judge marks True."""
    # Arrange
    raw_results = [
        {"url": "https://keep.example/a", "content": "snippet A"},
        {"url": "https://drop.example/b", "content": "snippet B"},
        {"url": "https://keep.example/c", "content": "snippet C"},
    ]
    chat_model = FakeJudgeChatModel(
        messages=iter([]),
        url_verdicts={
            "https://keep.example/a": True,
            "https://drop.example/b": False,
            "https://keep.example/c": True,
        },
    )

    async def run() -> list[str]:
        return await _filter_relevant_urls(
            chat_model,
            query="golang generics",
            raw_results=raw_results,
            semaphore=asyncio.Semaphore(3),
        )

    # Act
    kept = asyncio.run(run())

    # Assert
    assert kept == ["https://keep.example/a", "https://keep.example/c"]


def test_filter_relevant_urls_drops_urls_whose_judge_raised() -> None:
    """URLs that trigger exceptions during the gate should be dropped, not propagated."""
    # Arrange
    raw_results = [
        {"url": "https://ok.example/a", "content": "snippet A"},
        {"url": "https://boom.example/b", "content": "snippet B"},
        {"url": "https://ok.example/c"},
    ]
    chat_model = FakeJudgeChatModel(
        messages=iter([]),
        url_verdicts={
            "https://ok.example/a": True,
            "https://boom.example/b": RuntimeError,
            "https://ok.example/c": True,
        },
    )

    async def run() -> list[str]:
        return await _filter_relevant_urls(
            chat_model,
            query="rust borrow checker",
            raw_results=raw_results,
            semaphore=asyncio.Semaphore(3),
        )

    # Act
    kept = asyncio.run(run())

    # Assert - exception did not propagate and offending URL is absent
    with check:
        assert "https://boom.example/b" not in kept
    with check:
        assert set(kept) == {"https://ok.example/a", "https://ok.example/c"}


# endregion
