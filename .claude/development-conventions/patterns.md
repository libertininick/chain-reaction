# Patterns & Best Practices

## Composition Over Inheritance

**Prefer composition to build flexible, reusable code.**

### Why Composition Wins

| Issue with Inheritance | How Composition Helps |
|------------------------|----------------------|
| Tight coupling to parent | Components can be swapped independently |
| Deep hierarchies are fragile | Flat structures are easier to understand |
| Subclass explosion (N × M) | Compose N + M components instead |
| Hard to test in isolation | Components are independently testable |

### Example: Composable Processors

```python
from typing import Protocol

class Processor(Protocol):
    """Any object that can process data."""
    def process(self, data: Data) -> Result: ...

class LoggingProcessor:
    """Adds logging around any processor."""

    def __init__(self, wrapped: Processor, logger: Logger) -> None:
        self._wrapped = wrapped
        self._logger = logger

    def process(self, data: Data) -> Result:
        self._logger.info(f"Processing {data.id}")
        return self._wrapped.process(data)

# Compose at runtime
processor = LoggingProcessor(ValidatingProcessor(CoreProcessor(), validator), logger)
```

### Dependency Injection

```python
class SearchService:
    """Search service composed of independent components."""

    def __init__(self, embedder: Embedder, index: VectorIndex, ranker: ResultRanker) -> None:
        self._embedder = embedder
        self._index = index
        self._ranker = ranker

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        embedding = self._embedder.embed(query)
        candidates = self._index.find_similar(embedding, limit=limit * 2)
        return self._ranker.rank(candidates)[:limit]
```

### When Inheritance is Acceptable

- **Abstract base classes** defining contracts (`abc.ABC`)
- **Exception hierarchies** (`ChainReactionError` → `ValidationError`)
- **Framework requirements** (Pydantic `BaseModel`, dataclasses)

```python
class ChainReactionError(Exception):
    """Base for all domain errors."""

class ValidationError(ChainReactionError):
    """Raised when validation fails."""
```

---

## Error Handling

**Fail fast with clear, actionable error messages.**

### Clear Error Messages

```python
if not api_key:
    raise ValueError(
        "OPENAI_API_KEY environment variable not set. "
        "Set it with: export OPENAI_API_KEY='sk-...'"
    )
```

### Custom Exceptions

```python
class ChainReactionError(Exception):
    """Base exception for all chain-reaction errors."""

class ConfigurationError(ChainReactionError):
    """Raised when configuration is invalid or missing."""

class RetryableError(ChainReactionError):
    """Raised for errors that may succeed on retry."""
```

### Exception Chaining

Preserve context when re-raising:

```python
try:
    response = client.fetch(url)
except ConnectionError as e:
    raise RetryableError(f"Failed to connect to {url}") from e
```

### Guidelines

| Rule | Guidance |
|------|----------|
| Catch specific exceptions | Never use bare `except:` |
| Let unexpected exceptions propagate | Don't suppress unknown errors |
| Use exception chaining | `raise ... from e` preserves context |
| Avoid exceptions for control flow | Use return values instead |

---

## Pythonic Patterns

### Comprehensions

Use for simple transformations:

```python
names = [user.name for user in users if user.active]
scores_by_id = {item.id: item.score for item in results}
```

For complex logic, use explicit loops instead.

### Context Managers

Use for any resource that needs cleanup:

```python
from contextlib import contextmanager
from collections.abc import Iterator

@contextmanager
def timed_operation(name: str) -> Iterator[None]:
    """Context manager that logs operation duration."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info(f"{name} completed in {elapsed:.2f}s")
```

### Generators

Use for memory-efficient iteration:

```python
def read_chunks(path: Path, chunk_size: int = 8192) -> Iterator[bytes]:
    """Read file in chunks without loading entire file into memory."""
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk
```

### Structural Pattern Matching

Use for complex conditional logic on structured data:

```python
def handle_response(response: dict[str, Any]) -> Result:
    match response:
        case {"status": "ok", "data": data}:
            return Result.success(data)
        case {"status": "error", "code": code, "message": msg}:
            return Result.failure(code, msg)
        case _:
            raise ValueError(f"Unexpected response: {response}")
```
