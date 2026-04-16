"""Web search utilities using Tavily for search and trafilatura for content extraction.

Provides `async_web_search`, which queries Tavily, optionally filters results
for relevance with an LLM, then fetches and extracts the surviving pages as
markdown.

Examples:
    Basic search without LLM filtering:

    ```python
    import asyncio
    from tavily import AsyncTavilyClient
    from chain_reaction.web_search import async_web_search

    async def main():
        client = AsyncTavilyClient(api_key="tvly-...")
        results = await async_web_search("python async patterns", client)
        for r in results:
            print(r.url, r.content[:120])

    asyncio.run(main())
    ```

    With LLM-based relevance filtering before fetching:

    ```python
    from langchain.chat_models import init_chat_model

    results = await async_web_search(
        "python async patterns",
        client,
        judge_model=init_chat_model("gpt-4o-mini", model_provider="openai"),
    )
    ```
"""

from __future__ import annotations

import asyncio
from typing import cast

import httpx
import trafilatura
from langchain.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from pydantic import BaseModel
from tavily import AsyncTavilyClient


class SearchResult(BaseModel):
    """A web page fetched and extracted as markdown.

    Attributes:
        url (str): The source URL of the page.
        content (str): The main page content extracted as markdown.
    """

    url: str
    content: str


class RelevanceVerdict(BaseModel):
    """Structured LLM output for relevance filtering of a search result.

    Attributes:
        is_relevant (bool): Whether the search result is likely to contain
            substantial, useful information for the query.
    """

    is_relevant: bool


async def async_web_search(
    query: str,
    tavily_client: AsyncTavilyClient,
    judge_model: BaseChatModel | None = None,
    max_results: int = 5,
    max_concurrent: int = 5,
) -> list[SearchResult]:
    """Search the web, optionally filter results with an LLM, and return markdown content.

    Queries Tavily for search results. If `judge_model` is provided, uses it
    to judge which snippets are worth fetching; otherwise fetches every result.
    The surviving pages are downloaded in parallel and their main content is
    extracted as markdown.

    Args:
        query (str): The search query to send to Tavily.
        tavily_client (AsyncTavilyClient): Tavily client used for search.
        judge_model (BaseChatModel | None): Chat model for the relevance gate.
            When `None`, the LLM gate is skipped and all results are fetched.
        max_results (int): Maximum number of results to request from Tavily.
        max_concurrent (int): Maximum number of concurrent HTTP fetches and LLM
            relevance calls.

    Returns:
        list[SearchResult]: Pages that passed the relevance filter (if any) and
            were successfully fetched and extracted.
    """
    # Setup: shared concurrency limiter.
    semaphore = asyncio.Semaphore(max_concurrent)

    # Search: query Tavily for candidate results.
    response = await tavily_client.search(query, max_results=max_results)
    raw_results = response["results"]

    # Filter: keep URLs that passed the relevance gate (or all, if gate is off).
    if judge_model is None:
        urls_to_fetch = [r["url"] for r in raw_results]
    else:
        urls_to_fetch = await _filter_relevant_urls(judge_model, query, raw_results, semaphore)

    # Fetch: download and extract in parallel with throttling.
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as http:
        fetch_tasks = [_fetch_and_extract(http, url, semaphore) for url in urls_to_fetch]
        fetched = await asyncio.gather(*fetch_tasks)

    # Return: drop failed fetches.
    return [r for r in fetched if r is not None]


# region Helpers
async def _filter_relevant_urls(
    judge_model: BaseChatModel,
    query: str,
    raw_results: list[dict],
    semaphore: asyncio.Semaphore,
) -> list[str]:
    """Return URLs from `raw_results` that the LLM judges relevant to `query`."""
    judge = judge_model.with_structured_output(RelevanceVerdict)
    gate_tasks = [_is_worth_fetching(judge, query, r["url"], r.get("content", ""), semaphore) for r in raw_results]
    verdicts = await asyncio.gather(*gate_tasks, return_exceptions=True)
    return [
        r["url"]
        for r, v in zip(raw_results, verdicts, strict=True)
        if v is True  # skip exceptions and N verdicts
    ]


async def _is_worth_fetching(
    judge: Runnable,
    query: str,
    url: str,
    snippet: str,
    semaphore: asyncio.Semaphore,
) -> bool:
    """Use an LLM to decide if a search result merits a full download."""
    async with semaphore:
        verdict = await judge.ainvoke([
            {
                "role": "system",
                "content": (
                    "You are a relevance filter. Given a search query, a URL, "
                    "and a content snippet, decide whether the full page is likely "
                    "to contain substantial, useful information for the query."
                ),
            },
            {
                "role": "user",
                "content": f"Query: {query}\nURL: {url}\nSnippet: {snippet}",
            },
        ])
        return cast(RelevanceVerdict, verdict).is_relevant


async def _fetch_and_extract(
    client: httpx.AsyncClient,
    url: str,
    semaphore: asyncio.Semaphore,
) -> SearchResult | None:
    """Download a page and extract main content as markdown."""
    async with semaphore:
        try:
            resp = await client.get(url)
        except httpx.HTTPError:
            return None

    if not resp.is_success:
        return None

    main_content = trafilatura.extract(
        resp.text,
        output_format="markdown",
        include_links=True,
    )
    if not main_content:
        return None

    return SearchResult(url=url, content=main_content)


# endregion
