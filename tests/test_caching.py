"""Tests for the caching module in the chain_reaction package."""

from diskcache import Cache
from langchain.tools import tool

from chain_reaction.caching import cache_calls, evict_calls


def test_tool_caching() -> None:
    """Test caching of tool calls.

    1. Define a tool with caching decorator.
    2. Call the tool multiple times with the same and different arguments.
    3. Verify that cached results are returned for repeated calls with the same arguments.
    4. Clear the cache and verify that subsequent calls re-execute the tool.
    """
    # SETUP
    # Define temporary disk cache for caching tool calls
    cache = Cache()

    # Define a tool with caching decorator
    call_count: int = 0

    @tool
    @cache_calls(cache=cache)
    def tool_with_cache(x: float) -> float:
        """A tool that squares a number with simulated delay."""
        # Increment call count to track executions
        nonlocal call_count
        call_count += 1

        # Return function result
        return x * x

    # TEST
    # First call to the tool (should not be cached)
    result_1 = tool_with_cache.invoke({"x": 3.0})  # type: ignore
    assert result_1 == 9.0
    assert call_count == 1  # Ensure function was executed

    # Second call to the tool with the same argument (should be cached)
    result_2 = tool_with_cache.invoke({"x": 3.0})
    assert result_2 == 9.0
    assert call_count == 1  # Ensure function was not executed again

    # Third call to the tool with a different argument (should not be cached)
    result_3 = tool_with_cache.invoke({"x": 4.0})
    assert result_3 == 16.0
    assert call_count == 2  # Ensure function was executed again

    # Clear cache
    num_cleared = evict_calls(cache=cache, func=tool_with_cache)
    assert num_cleared == 2  # Two entries should have been cleared

    # Fourth call to the tool with the first argument again (should not be cached)
    result_4 = tool_with_cache.invoke({"x": 3.0})
    assert result_4 == 9.0
    assert call_count == 3  # Ensure function was executed again


def test_evict_calls_from_cache() -> None:
    """Test eviction of cached function calls.

    1. Define a function with caching decorator.
    2. Call the function multiple times to populate the cache.
    3. Evict cached calls for the function.
    4. Verify that the cache is cleared and subsequent calls re-execute the function.
    """
    # SETUP
    # Define temporary disk cache for caching tool calls
    cache = Cache()

    # Define cached functions
    call_counts: dict[str, int] = {}

    @cache_calls(cache=cache)
    def func1(x: float) -> float:
        """A tool that squares a number."""
        nonlocal call_counts
        call_counts["func1"] = call_counts.get("func1", 0) + 1
        return x * x

    @cache_calls(cache=cache)
    def func2(x: float) -> float:
        """A tool that squares a number."""
        nonlocal call_counts
        call_counts["func2"] = call_counts.get("func2", 0) + 1
        return x * x

    # Populate the cache with multiple calls
    func1(2.0)
    func1(3.0)
    assert call_counts["func1"] == 2  # Ensure func1 was executed twice

    func2(2.0)
    func2(3.0)
    assert call_counts["func2"] == 2  # Ensure func2 was executed twice

    # TEST
    # Evict cached calls for the function
    num_cleared = evict_calls(cache=cache, func=func2)
    assert num_cleared == 2  # Two entries should have been cleared

    # Call func2 again to verify it re-executes
    func2(2.0)
    assert call_counts["func2"] == 3  # Ensure func2 was executed again after eviction

    # Call func1 again to verify it is still cached
    func1(2.0)
    assert call_counts["func1"] == 2  # Ensure func1 was not executed


def test_caching_is_skipped_when_no_cache_provided() -> None:
    """Test that caching is skipped when no cache is provided.

    1. Define a function with caching decorator but no cache.
    2. Call the function multiple times.
    3. Verify that the function is executed each time (no caching).
    """
    # SETUP
    # Define cached function without providing a cache
    call_count: int = 0

    @cache_calls(cache=None)
    def func_no_cache(x: float) -> float:
        """A tool that squares a number."""
        nonlocal call_count
        call_count += 1
        return x * x

    # TEST
    # Call the function multiple times
    result_1 = func_no_cache(2.0)
    assert result_1 == 4.0
    assert call_count == 1  # Ensure function was executed

    result_2 = func_no_cache(2.0)
    assert result_2 == 4.0
    assert call_count == 2  # Ensure function was executed again

    result_3 = func_no_cache(3.0)
    assert result_3 == 9.0
    assert call_count == 3  # Ensure function was executed again
