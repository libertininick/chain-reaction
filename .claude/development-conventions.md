# Development Conventions

## Guiding Principles

| Principle | Guidance |
|-----------|----------|
| Simplicity | Prioritize readable code. NEVER over-engineer. |
| PEP 8 | Follow strictly. Format with `ruff format`. |
| Explicitness | Avoid magic. Be explicit about types, defaults, and behavior. |
| Locality | Keep related code together. Minimize distance between definition and usage. |

## Validation Commands

```bash
uv run ruff check --fix && uv run ruff format  # Lint and format
uv run ty check .                               # Type check
uv run pytest --cov --cov-fail-under=90         # Tests with coverage
uv tool run pydoclint --style=google --allow-init-docstring=True src/ tests/  # Docstrings
```

## Code Organization

### Principles

- Organize code into clearly separated modules, grouped by feature or responsibility
- Use consistent naming conventions, file structure, and architecture patterns
- Code should be organized into discrete, testable units that are easy to maintain and refactor
- Use composition over inheritance
- Follow DRY, but NEVER create tight coupling just to avoid repetition
- No circular dependencies between modules
- Each function/class should have one clear purpose

### Module Design

- **Module size**: Split when a file exceeds ~300-500 lines or has multiple unrelated responsibilities
- **Public API**: Use `__all__` to define explicit public interfaces
- **Private members**: Prefix with `_` for internal implementation details
- **Imports in `__init__.py`**: Re-export only the public API, keep it minimal

```python
# src/chain_reaction/retrieval/__init__.py
from chain_reaction.retrieval.embeddings import EmbeddingModel
from chain_reaction.retrieval.search import SemanticSearch

__all__ = ["EmbeddingModel", "SemanticSearch"]
```

### Import Organization

Organize imports in this order (enforced by [ruff](../pyproject.toml)):

1. Standard library
2. Third-party packages
3. Local application imports

```python
# Good - clear grouping, absolute imports
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from pydantic import BaseModel

from chain_reaction.core import Config
from chain_reaction.utils import validate_input
```

Use absolute imports. Avoid `from module import *`.

## Naming Conventions

**Names should reveal intent and be self-documenting.**

### Function and Method Names

Use the `<verb>_<noun>` pattern to clearly communicate what the function does:

```python
# Good - verb_noun pattern reveals intent
def fetch_user(user_id: int) -> User: ...
def calculate_similarity(vec_a: list[float], vec_b: list[float]) -> float: ...
def validate_config(config: Config) -> bool: ...
def parse_response(raw: str) -> Response: ...
def build_query(filters: list[Filter]) -> Query: ...

# Bad - vague or missing verb
def user(user_id: int) -> User: ...  # What action?
def similarity(vec_a, vec_b): ...     # Calculate? Check? Compare?
def config(config: Config): ...       # Validate? Load? Save?
def response(raw: str): ...           # Parse? Build? Send?
```

### Common Verb Prefixes

| Verb | Use For | Example |
|------|---------|---------|
| `get_` | Retrieve existing data | `get_user_by_id`, `get_config` |
| `fetch_` | Retrieve from external source | `fetch_api_data`, `fetch_remote_file` |
| `create_` | Instantiate new objects | `create_session`, `create_embedding` |
| `build_` | Construct complex objects | `build_query`, `build_request` |
| `parse_` | Convert/interpret data | `parse_json`, `parse_response` |
| `validate_` | Check correctness | `validate_input`, `validate_schema` |
| `calculate_` | Compute values | `calculate_score`, `calculate_distance` |
| `transform_` | Convert between formats | `transform_coordinates`, `transform_data` |
| `is_` / `has_` | Boolean checks | `is_valid`, `has_permission` |
| `async_` | Async functions | `async_fetch_data`, `async_process_batch` |

### Async Functions

Prefix async functions with `async_`:

```python
async def async_fetch_data(url: str) -> Response:
    """Fetch data asynchronously."""
    ...

async def async_process_batch(items: list[Item]) -> list[Result]:
    """Process items concurrently."""
    ...
```

### Variable Names

```python
# Good - descriptive, reveals content/purpose
user_count = len(users)
max_retry_attempts = 3
embedding_dimensions = 768
is_authenticated = True
has_valid_license = check_license(user)

# Bad - single letters, abbreviations, generic names
n = len(users)       # What is n?
max = 3              # Max of what? (also shadows builtin)
dim = 768            # Dimension of what?
flag = True          # What flag?
temp = check(user)   # Temporary what?
```

### Class Names

Use `PascalCase` nouns that describe what the class represents:

```python
# Good - clear nouns describing the entity
class SearchIndex: ...
class EmbeddingModel: ...
class RetryPolicy: ...
class ValidationError: ...

# Bad - vague or verb-like names
class Manager: ...      # Manager of what?
class Helper: ...       # Too generic
class DoSearch: ...     # Verb, not noun
class Misc: ...         # Meaningless
```

### Constants

Use `SCREAMING_SNAKE_CASE` with descriptive names. Use `Final` for type-checked immutability:

```python
from typing import Final

# Good - clear purpose with Final annotation
MAX_RETRY_ATTEMPTS: Final = 3
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
SUPPORTED_FILE_FORMATS: Final[frozenset[str]] = frozenset({"json", "csv", "parquet"})

# Bad - unclear or too short
MAX = 3              # Max of what?
TIMEOUT = 30.0       # In what units?
FORMATS = {...}      # What kind of formats?
```

### Guidelines Summary

| Element | Convention | Example |
|---------|------------|---------|
| Functions/methods | `verb_noun` lowercase | `fetch_user`, `validate_input` |
| Async functions | `async_` prefix | `async_fetch_data` |
| Variables | `snake_case`, descriptive | `user_count`, `is_valid` |
| Classes | `PascalCase` nouns | `SearchIndex`, `UserSession` |
| Constants | `SCREAMING_SNAKE_CASE` + `Final` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private members | `_` prefix | `_internal_cache`, `_validate` |
| Type aliases | `PascalCase` | `JsonValue`, `Embedding` |

## Type Safety

**IMPORTANT: Type annotations are REQUIRED on all functions and classes.**

### Modern Type Hints (Python 3.10+)

```python
# Use union syntax, not Optional
def get_user(user_id: int) -> User | None:  # Not Optional[User]
    ...

# Use lowercase builtins for generics
def process(items: list[str]) -> dict[str, int]:  # Not List, Dict
    ...

# Use collections.abc for abstract container types
from collections.abc import Sequence, Mapping, Callable, Iterator, Iterable

def transform(items: Sequence[str]) -> Mapping[str, int]:
    ...

def apply(fn: Callable[[int], str], values: Iterable[int]) -> Iterator[str]:
    ...
```

### Generic Types

```python
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

def first(items: Sequence[T]) -> T | None:
    """Return the first item or None if empty."""
    return items[0] if items else None

def merge_dicts(a: dict[K, V], b: dict[K, V]) -> dict[K, V]:
    """Merge two dictionaries, with b taking precedence."""
    return {**a, **b}
```

### Self Type (Python 3.11+)

```python
from typing import Self

class Builder:
    """Fluent builder pattern with proper typing."""

    def with_name(self, name: str) -> Self:
        self.name = name
        return self

    def with_value(self, value: int) -> Self:
        self.value = value
        return self
```

### Protocol for Structural Subtyping

Use `Protocol` to define interfaces based on behavior (duck typing with type safety):

```python
from typing import Protocol

class Readable(Protocol):
    """Any object that can be read."""

    def read(self) -> str: ...

class Closeable(Protocol):
    """Any object that can be closed."""

    def close(self) -> None: ...

def process_stream(stream: Readable & Closeable) -> str:
    """Process any readable, closeable stream."""
    try:
        return stream.read()
    finally:
        stream.close()
```

### Type Aliases

```python
from typing import TypeAlias

# Simple alias for complex types
JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
Embedding: TypeAlias = list[float]
BatchEmbeddings: TypeAlias = list[Embedding]

def encode(texts: list[str]) -> BatchEmbeddings:
    ...
```

### Guidelines

| Rule | Guidance |
|------|----------|
| Avoid `Any` | Only use at true system boundaries (e.g., JSON parsing) |
| Prefer `X | None` | Over `Optional[X]` for clarity |
| Use `Sequence` | Over `list` in parameters when you only need iteration |
| Use `Mapping` | Over `dict` in parameters when you only need read access |
| Return concrete types | Return `list`, `dict` but accept `Sequence`, `Mapping` |

## Function Design

### Parameter Guidelines

- **Limit parameters**: Max 5 positional parameters; use dataclasses/Pydantic for more
- **Keyword-only arguments**: Use `*` to force keyword arguments for clarity
- **Return early**: Reduce nesting with guard clauses
- **Pure functions**: Prefer functions without side effects when possible
- **Return values over mutation**: Return values rather than modifying state when possible
- **Separate I/O from logic**: Keep business logic pure; isolate I/O operations at boundaries

```python
# Good - keyword-only after *, clear intent, documented defaults
def fetch_data(
    url: str,
    *,
    timeout: float = 30.0,
    retries: int = 3,
    headers: dict[str, str] | None = None,
) -> Response:
    """Fetch data from URL with retry logic.

    Args:
        url (str): The URL to fetch.
        timeout (float): Request timeout in seconds.
        retries (int): Number of retry attempts.
        headers (dict[str, str] | None): Optional HTTP headers.

    Returns:
        Response: The HTTP response.
    """
    ...
```

### Early Returns

Reduce nesting with guard clauses:

```python
# Good - early return reduces nesting
def process(data: Data | None) -> Result:
    if data is None:
        return Result.empty()

    if not data.is_valid:
        raise ValidationError(f"Invalid data: {data.error}")

    # Main logic at base indentation level
    return Result.from_data(data)


# Bad - deep nesting obscures main logic
def process(data: Data | None) -> Result:
    if data is not None:
        if data.is_valid:
            # Main logic buried in nesting
            return Result.from_data(data)
        else:
            raise ValidationError(f"Invalid data: {data.error}")
    else:
        return Result.empty()
```

## Data Structures

**Use Pydantic models or dataclasses instead of raw dictionaries.**

Structured data classes provide:

- **IDE support**: Autocompletion, refactoring, go-to-definition
- **Validation**: Automatic type checking and data validation (Pydantic)
- **Documentation**: Self-documenting field names and types
- **Immutability**: Prevent accidental mutations with `frozen=True`
- **Serialization**: Built-in JSON/dict conversion

```python
from pydantic import BaseModel, Field

# Good - Pydantic model with validation and documentation
class SearchResult(BaseModel):
    """A single search result from the retrieval system."""

    document_id: str = Field(description="Unique identifier for the document")
    content: str = Field(description="The matched text content")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score")
    metadata: dict[str, str] = Field(default_factory=dict)


def search(query: str) -> list[SearchResult]:
    ...


# Usage - clear attribute access with IDE support
results = search("python async")
for result in results:
    print(f"{result.document_id}: {result.score:.2f}")
```

```python
# Bad - raw dictionary with no validation or documentation
def search(query: str) -> list[dict]:
    ...

# Usage - error-prone string keys, no autocompletion
results = search("python async")
for result in results:
    print(f"{result['doc_id']}: {result['score']:.2f}")  # KeyError: 'doc_id'
```

### Configuration with Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment."""

    openai_api_key: str
    database_url: str
    debug: bool = False
    max_workers: int = 4

    model_config = {"env_prefix": "APP_"}
```

### When to Use Each

- **Pydantic**: Validation, serialization, API boundaries, configuration
- **dataclass**: Simple internal data containers, performance-critical code
- **dataclass(frozen=True)**: Immutable value objects, hashable keys

## Error Handling

**Fail fast with clear, actionable error messages. Validate inputs early at system boundaries.**

### Clear Error Messages

```python
# Good - clear context for debugging
if not api_key:
    raise ValueError(
        "OPENAI_API_KEY environment variable not set. "
        "Set it with: export OPENAI_API_KEY='sk-...'"
    )

# Bad - vague error
if not api_key:
    raise ValueError("Invalid configuration")
```

### Custom Exceptions

Define domain-specific exceptions for recoverable errors:

```python
class ChainReactionError(Exception):
    """Base exception for all chain-reaction errors."""


class ConfigurationError(ChainReactionError):
    """Raised when configuration is invalid or missing."""


class ValidationError(ChainReactionError):
    """Raised when input validation fails."""


class RetryableError(ChainReactionError):
    """Raised for errors that may succeed on retry."""
```

### Exception Chaining

Preserve context when re-raising:

```python
# Good - exception chaining preserves original traceback
try:
    response = client.fetch(url)
except ConnectionError as e:
    raise RetryableError(f"Failed to connect to {url}") from e

# Bad - loses original context
try:
    response = client.fetch(url)
except ConnectionError:
    raise RetryableError(f"Failed to connect to {url}")
```

### Guidelines

| Rule | Guidance |
|------|----------|
| Catch specific exceptions | Never use bare `except:` |
| Let unexpected exceptions propagate | Don't catch and suppress unknown errors |
| Use exception chaining | `raise ... from e` to preserve context |
| Avoid exceptions for control flow | Use return values or pattern matching |

## Documentation

**All public functions/classes/modules MUST have Google-style docstrings.**

- Explain the **why**, not the how
- Include example usage when helpful (tested by doctest)

```python
def calculate_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    """Calculate cosine similarity between two embeddings.

    Use this for comparing semantic similarity of text chunks when building
    retrieval systems. Values closer to 1.0 indicate higher similarity.

    Args:
        embedding_a (list[float]): First embedding vector.
        embedding_b (list[float]): Second embedding vector.

    Returns:
        float: Cosine similarity score between -1.0 and 1.0.

    Raises:
        ValueError: If vectors have different dimensions.

    Example:
        >>> calculate_similarity([1.0, 0.0], [1.0, 0.0])
        1.0
        >>> calculate_similarity([1.0, 0.0], [0.0, 1.0])
        0.0
    """
```

### When to Use Comments vs Docstrings

- **Docstrings**: Public API documentation (functions, classes, modules)
- **Comments**: Explain *why* for non-obvious implementation details

```python
# Good - comment explains WHY, not what
# Use binary search here because the list is sorted and can have 100k+ items
index = bisect.bisect_left(sorted_items, target)

# Bad - comment restates the code
# Increment counter by 1
counter += 1
```

## Pythonic Patterns

### Comprehensions

Use for simple transformations; prefer explicit loops for complex logic:

```python
# Good - clear transformation
names = [user.name for user in users if user.active]

# Good - dict comprehension
scores_by_id = {item.id: item.score for item in results}

# Bad - too complex, use a loop instead
result = [transform(x) for x in data if condition(x) and validate(x) or fallback(x)]
```

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


# Usage
with timed_operation("data_processing"):
    process_large_dataset(data)
```

### Generators

Use for memory-efficient iteration over large datasets:

```python
def read_chunks(path: Path, chunk_size: int = 8192) -> Iterator[bytes]:
    """Read file in chunks without loading entire file into memory."""
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk
```

### Structural Pattern Matching (Python 3.10+)

Use for complex conditional logic on structured data:

```python
from typing import Any

def handle_response(response: dict[str, Any]) -> Result:
    """Handle API response with pattern matching."""
    match response:
        case {"status": "ok", "data": data}:
            return Result.success(data)
        case {"status": "error", "code": code, "message": msg}:
            return Result.failure(code, msg)
        case {"status": "pending", "retry_after": seconds}:
            return Result.pending(retry_after=seconds)
        case _:
            raise ValueError(f"Unexpected response format: {response}")
```

## Testing

### Test Organization

- Mirror source structure: `src/module/feature.py` → `tests/module/test_feature.py`
- One test file per source module
- Group related tests in classes when they share setup

```
src/
  chain_reaction/
    retrieval/
      embeddings.py
      search.py
tests/
  retrieval/
    test_embeddings.py
    test_search.py
```

### Test Naming

Pattern: `test_<function>_<scenario>_<expected_result>`

```python
def test_calculate_similarity_identical_vectors_returns_one() -> None:
    """Identical vectors should have similarity of 1.0."""
    vec = [1.0, 0.0, 0.0]
    assert calculate_similarity(vec, vec) == 1.0


def test_calculate_similarity_orthogonal_vectors_returns_zero() -> None:
    """Orthogonal vectors should have similarity of 0.0."""
    assert calculate_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_calculate_similarity_mismatched_dimensions_raises_value_error() -> None:
    """Vectors with different dimensions should raise ValueError."""
    with pytest.raises(ValueError, match="dimension"):
        calculate_similarity([1.0, 0.0], [1.0, 0.0, 0.0])
```

### Test Structure

Follow Arrange-Act-Assert pattern:

```python
def test_search_returns_results_sorted_by_score() -> None:
    """Search results should be sorted by relevance score descending."""
    # Arrange
    index = SearchIndex()
    index.add_documents(sample_documents)

    # Act
    results = index.search("python async", limit=10)

    # Assert
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
```

### Fixtures

Keep fixtures close to their usage. Use `conftest.py` only for widely shared fixtures:

```python
# tests/retrieval/conftest.py - shared across retrieval tests
@pytest.fixture
def sample_embeddings() -> list[list[float]]:
    """Sample embeddings for testing."""
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


# tests/retrieval/test_search.py - local fixture
@pytest.fixture
def populated_index(sample_embeddings: list[list[float]]) -> SearchIndex:
    """Search index populated with sample data."""
    index = SearchIndex()
    for i, emb in enumerate(sample_embeddings):
        index.add(f"doc_{i}", emb)
    return index
```

### Parametrized Tests

Use parametrize for testing multiple inputs:

```python
@pytest.mark.parametrize(
    ("input_text", "expected_tokens"),
    [
        ("hello world", ["hello", "world"]),
        ("", []),
        ("  spaces  ", ["spaces"]),
        ("UPPERCASE", ["uppercase"]),
    ],
)
def test_tokenize(input_text: str, expected_tokens: list[str]) -> None:
    """Tokenizer should handle various input formats."""
    assert tokenize(input_text) == expected_tokens
```

### Coverage Requirements

- Aim for >=90% coverage on core logic
- 100% coverage on public APIs

### Testing Anti-Patterns

Avoid these common testing mistakes:

| Anti-Pattern | Guidance |
|--------------|----------|
| Coverage-driven tests | Don't write tests solely to increase coverage percentage. Test meaningful behavior. |
| Implementation testing | Test observable behavior, not implementation details. Tests should survive refactoring. |
| Single-use fixtures | Don't create fixtures for single-use data. Define inline for clarity. |
| Fixture duplication | Don't duplicate existing fixtures. Extend or generalize them instead. |
| Order-dependent tests | Tests must be independent. Never rely on execution order or shared state. |
| Over-abstracted utilities | Keep tests readable and self-contained. Avoid excessive test helper abstractions. |
| Superficial type checks | Don't write superficial `isinstance` checks unless validating critical type safety. |

### Test Examples

#### Example 1: Simple Unit Test with Type Hints and Documentation

```python
from pytest_check import check_functions
from mymodule import calculate_total


def test_calculate_total_with_valid_items() -> None:
    """Test that calculate_total correctly sums item prices.

    Verifies that the function properly handles a list of items with prices
    and returns the correct total, including proper decimal handling.
    """
    items: list[dict[str, float]] = [
        {"name": "apple", "price": 1.50},
        {"name": "banana", "price": 0.75},
        {"name": "orange", "price": 2.00},
    ]

    result: float = calculate_total(items)

    check_functions.equal(result, 4.25)
```

#### Example 2: Parameterized Tests

```python
import pytest
from pytest_check import check_functions
from mymodule import validate_email


@pytest.mark.parametrize(
    ("email", "expected_valid"),
    [
        # Valid emails
        ("user@example.com", True),
        ("test.user+tag@domain.co.uk", True),
        ("123@test.com", True),
        # Invalid emails
        ("", False),
        ("invalid", False),
        ("@example.com", False),
        ("user@", False),
        ("user @example.com", False),
    ],
    ids=[
        "simple_valid",
        "complex_valid",
        "numeric_valid",
        "empty_string",
        "no_at_symbol",
        "missing_local_part",
        "missing_domain",
        "contains_space",
    ],
)
def test_validate_email(email: str, expected_valid: bool) -> None:
    """Test email validation with various valid and invalid formats.

    Ensures the validator correctly identifies valid email addresses and rejects
    common invalid patterns like missing components or invalid characters.

    Args:
        email: Email address to validate
        expected_valid: Whether the email should be considered valid
    """
    result: bool = validate_email(email)


    check_functions.equal(
        result,
        expected_valid,
        msg=f"Expected {email!r} to be {'valid' if expected_valid else 'invalid'}",
    )
```

#### Example 3: Test Class for Grouping Related Tests

```python
from pathlib import Path
from typing import Any

import pytest
from pytest_check import check_functions
from mymodule import DataProcessor


class TestDataProcessor:
    """Test suite for DataProcessor class.

    Groups all tests related to the DataProcessor functionality including
    initialization, data loading, transformation, and error handling.
    """

    @pytest.fixture
    def processor(self) -> DataProcessor:
        """Create a DataProcessor instance for testing.

        Returns:
            A configured DataProcessor with test settings
        """
        return DataProcessor(max_size=1000, validate=True)

    @pytest.fixture
    def sample_data(self) -> list[dict[str, Any]]:
        """Provide sample data for testing.

        Returns:
            List of sample records with various data types
        """
        return [
            {"id": 1, "value": 10.5, "name": "test1"},
            {"id": 2, "value": 20.0, "name": "test2"},
            {"id": 3, "value": 15.7, "name": "test3"},
        ]

    def test_processor_initialization(self) -> None:
        """Test DataProcessor initializes with correct default values.

        Verifies that the processor sets up with expected configuration
        and that all required attributes are properly initialized.
        """
        processor = DataProcessor()

        check_functions.is_not_none(processor)
        check_functions.equal(processor.max_size, 10000)  # default
        check_functions.is_true(processor.validate)  # default

    def test_load_data_success(
        self,
        processor: DataProcessor,
        sample_data: list[dict[str, Any]],
    ) -> None:
        """Test successful data loading with valid input.

        Ensures the processor correctly loads and stores valid data,
        maintaining data integrity and proper record count.

        Args:
            processor: DataProcessor fixture instance
            sample_data: Sample data fixture
        """
        processor.load_data(sample_data)

        check_functions.equal(processor.record_count, 3)
        check_functions.equal(processor.data, sample_data)
        check_functions.is_true(processor.is_loaded)

    def test_load_data_empty_list(self, processor: DataProcessor) -> None:
        """Test data loading with empty list.

        Verifies the processor handles empty input gracefully without errors
        and sets appropriate state.

        Args:
            processor: DataProcessor fixture instance
        """
        processor.load_data([])

        check_functions.equal(processor.record_count, 0)
        check_functions.is_false(processor.is_loaded)

    def test_load_data_exceeds_max_size(self, processor: DataProcessor) -> None:
        """Test that loading data exceeding max_size raises ValueError.

        Ensures the processor enforces size limits and provides a clear
        error message when limits are exceeded.

        Args:
            processor: DataProcessor fixture instance
        """
        large_data = [{"id": i} for i in range(2000)]

        with pytest.raises(ValueError, match="exceeds maximum size"):
            processor.load_data(large_data)

    @pytest.mark.parametrize(
        ("transform_type", "expected_sum"),
        [
            ("double", 92.4),  # (10.5 + 20.0 + 15.7) * 2
            ("square", 748.54),  # 10.5^2 + 20.0^2 + 15.7^2
            ("identity", 46.2),  # 10.5 + 20.0 + 15.7
        ],
        ids=["double_values", "square_values", "identity_transform"],
    )
    def test_transform_data(
        self,
        processor: DataProcessor,
        sample_data: list[dict[str, Any]],
        transform_type: str,
        expected_sum: float,
    ) -> None:
        """Test data transformation with different transformation types.

        Verifies that various transformation operations correctly modify
        the data values while preserving data structure.

        Args:
            processor: DataProcessor fixture instance
            sample_data: Sample data fixture
            transform_type: Type of transformation to apply
            expected_sum: Expected sum of transformed values
        """
        processor.load_data(sample_data)
        transformed = processor.transform(transform_type)

        actual_sum = sum(item["value"] for item in transformed)

        check_functions.equal(len(transformed), 3)
        check_functions.almost_equal(actual_sum, expected_sum, rel=1e-2)

    def test_transform_without_loading_data(self, processor: DataProcessor) -> None:
        """Test that transforming without loaded data raises RuntimeError.

        Ensures the processor validates state before operations and provides
        clear error messages for incorrect usage.

        Args:
            processor: DataProcessor fixture instance
        """
        with pytest.raises(RuntimeError, match="No data loaded"):
            processor.transform("double")
```

## Common Mistakes

Avoid these patterns that cause subtle bugs or maintenance issues:

### Mutable Default Arguments

```python
# Bad - mutable default argument
def add_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)  # Mutates shared default!
    return items

# Good - use None and create new list
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

### Commented-Out Code

Use version control instead of leaving dead code in the codebase. Commented-out code creates confusion about what's active.

### Implicit Dependencies

Make dependencies explicit through function parameters or constructor injection. Hidden dependencies make code hard to test and reason about.

### Premature Abstraction

Don't create abstractions for single-use cases. Three similar lines of code is better than a premature abstraction. Reuse or extend existing functionality before creating new code.

### Speculative Features

Don't add features "just in case" they might be needed later. Only implement what's needed now. YAGNI (You Aren't Gonna Need It).

### Overly Broad Error Handling

Don't add generic error handling that obscures real errors. Catch specific exceptions and let unexpected errors propagate with full context.
