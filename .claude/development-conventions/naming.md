# Naming Conventions

**Names should reveal intent and be self-documenting.**

## Function and Method Names

Use the `<verb>_<noun>` pattern:

```python
def fetch_user(user_id: int) -> User: ...
def calculate_similarity(vec_a: list[float], vec_b: list[float]) -> float: ...
def validate_config(config: Config) -> bool: ...
def parse_response(raw: str) -> Response: ...
```

## Common Verb Prefixes

| Verb | Use For | Example |
|------|---------|---------|
| `get_` | Retrieve existing data | `get_user_by_id`, `get_config` |
| `fetch_` | Retrieve from external source | `fetch_api_data`, `fetch_remote_file` |
| `create_` | Instantiate new objects | `create_session`, `create_embedding` |
| `build_` | Construct complex objects | `build_query`, `build_request` |
| `parse_` | Convert/interpret data | `parse_json`, `parse_response` |
| `validate_` | Check correctness | `validate_input`, `validate_schema` |
| `calculate_` | Compute values | `calculate_score`, `calculate_distance` |
| `transform_` | Convert between formats | `transform_coordinates` |
| `is_` / `has_` | Boolean checks | `is_valid`, `has_permission` |
| `async_` | Async functions (prefix) | `async_fetch_user`, `async_process_batch` |

## Async Functions

Prefix async functions with `async_` to make the async nature visible at call sites:

```python
async def async_fetch_user(user_id: int) -> User:
    return await client.get(f"/users/{user_id}")

async def async_process_batch(items: list[Item]) -> list[Result]:
    return await asyncio.gather(*[async_process(item) for item in items])
```

This makes it immediately clear when reviewing code that `await` is required.

## Variable Names

```python
# Good - descriptive, reveals content/purpose
user_count = len(users)
max_retry_attempts = 3
embedding_dimensions = 768
is_authenticated = True
has_valid_license = check_license(user)
```

Avoid single letters, abbreviations, and generic names like `temp`, `data`, `flag`.

## Class Names

Use `PascalCase` nouns that describe what the class represents:

```python
class SearchIndex: ...
class EmbeddingModel: ...
class RetryPolicy: ...
class ValidationError: ...
```

## Constants

Use `SCREAMING_SNAKE_CASE` with `Final` for type-checked immutability:

```python
from typing import Final

MAX_RETRY_ATTEMPTS: Final = 3
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
SUPPORTED_FILE_FORMATS: Final[frozenset[str]] = frozenset({"json", "csv", "parquet"})
```

## Private Members

Prefix with `_` for internal implementation details:

```python
class SearchService:
    def __init__(self, index: VectorIndex) -> None:
        self._index = index  # Private
        self._cache: dict[str, Result] = {}  # Private

    def search(self, query: str) -> list[Result]:  # Public API
        return self._perform_search(query)

    def _perform_search(self, query: str) -> list[Result]:  # Private helper
        ...
```

## Summary Table

| Element | Convention | Example |
|---------|------------|---------|
| Functions/methods | `verb_noun` lowercase | `fetch_user`, `validate_input` |
| Variables | `snake_case`, descriptive | `user_count`, `is_valid` |
| Classes | `PascalCase` nouns | `SearchIndex`, `UserSession` |
| Constants | `SCREAMING_SNAKE_CASE` + `Final` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private members | `_` prefix | `_internal_cache`, `_validate` |
| Type aliases | `PascalCase` | `JsonValue`, `Embedding` |
