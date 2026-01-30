---
name: testing
description: Pytest testing conventions for this codebase. Apply when writing or reviewing tests including test naming, structure, fixtures, and parametrization.
user-invocable: false
---

# Testing Conventions

Pytest conventions for writing maintainable, behavior-focused tests.

## Quick Reference

| Element | Convention |
|---------|------------|
| Test file naming | `test_<module>.py` |
| Test function naming | `test_<function>_<scenario>_<expected>` |
| Test structure | Arrange-Act-Assert with comments |
| Fixtures | Local unless shared across multiple test files |
| Multiple inputs | Use `@pytest.mark.parametrize` |
| Related tests | Group in test classes |

## Anti-Patterns to Avoid

| Anti-Pattern | Guidance |
|--------------|----------|
| Coverage-driven tests | Test meaningful behavior, not lines |
| Implementation testing | Test observable behavior; tests should survive refactoring |
| Order-dependent tests | Tests must be independent; never rely on execution order |
| Single-use fixtures | Define test data inline for clarity |
| Fixture duplication | Extend or generalize existing fixtures |

## Test Organization

Mirror source structure:

```
src/chain_reaction/retrieval/embeddings.py
tests/retrieval/test_embeddings.py
```

## Test Naming

**Pattern**: `test_<function>_<scenario>_<expected_result>`

```python
# CORRECT - descriptive name following pattern
def test_calculate_similarity_identical_vectors_returns_one() -> None:
    """Identical vectors should have similarity of 1.0."""
    vec = [1.0, 0.0, 0.0]
    assert calculate_similarity(vec, vec) == 1.0


def test_calculate_similarity_mismatched_dimensions_raises_value_error() -> None:
    """Vectors with different dimensions should raise ValueError."""
    with pytest.raises(ValueError, match="dimension"):
        calculate_similarity([1.0, 0.0], [1.0, 0.0, 0.0])


# INCORRECT - vague names
def test_similarity():  # Missing scenario and expected result
    ...

def test_error():  # No context about what's being tested
    ...
```

## Test Structure: Arrange-Act-Assert

Always organize tests with clear AAA sections:

```python
# CORRECT - clear AAA structure with comments
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


# INCORRECT - mixed arrangement and assertions
def test_search_sorting() -> None:
    index = SearchIndex()
    assert index is not None  # Asserting during arrangement
    index.add_documents(sample_documents)
    results = index.search("python async", limit=10)
    assert len(results) > 0
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
```

## Fixtures

Keep fixtures close to their usage. Use `conftest.py` only for widely shared fixtures.

```python
# CORRECT - shared fixture in conftest.py
# tests/retrieval/conftest.py
@pytest.fixture
def sample_embeddings() -> list[list[float]]:
    """Sample embeddings for testing."""
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


# CORRECT - local fixture extending shared fixture
# tests/retrieval/test_search.py
@pytest.fixture
def populated_index(sample_embeddings: list[list[float]]) -> SearchIndex:
    """Search index populated with sample data."""
    index = SearchIndex()
    for i, emb in enumerate(sample_embeddings):
        index.add(f"doc_{i}", emb)
    return index


# INCORRECT - single-use fixture that should be inline
@pytest.fixture
def single_vector() -> list[float]:
    return [1.0, 0.0, 0.0]

def test_something(single_vector):  # Just define inline instead
    ...
```

## Parametrized Tests

Use for testing multiple inputs with the same logic:

```python
# CORRECT - parametrized test with descriptive IDs
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


# INCORRECT - separate tests for each case
def test_tokenize_simple():
    assert tokenize("hello world") == ["hello", "world"]

def test_tokenize_empty():
    assert tokenize("") == []

def test_tokenize_spaces():
    assert tokenize("  spaces  ") == ["spaces"]
```

## Test Classes

Group related tests in classes with shared fixtures:

```python
class TestDataProcessor:
    """Test suite for DataProcessor class."""

    @pytest.fixture
    def processor(self) -> DataProcessor:
        """Create a DataProcessor instance for testing."""
        return DataProcessor(max_size=1000, validate=True)

    @pytest.fixture
    def sample_data(self) -> list[dict[str, Any]]:
        """Provide sample data for testing."""
        return [
            {"id": 1, "value": 10.5, "name": "test1"},
            {"id": 2, "value": 20.0, "name": "test2"},
        ]

    def test_load_data_success(
        self, processor: DataProcessor, sample_data: list[dict[str, Any]]
    ) -> None:
        """Test successful data loading with valid input."""
        processor.load_data(sample_data)

        assert processor.record_count == 2
        assert processor.is_loaded

    def test_load_data_exceeds_max_size(self, processor: DataProcessor) -> None:
        """Test that loading data exceeding max_size raises ValueError."""
        large_data = [{"id": i} for i in range(2000)]

        with pytest.raises(ValueError, match="exceeds maximum size"):
            processor.load_data(large_data)
```

## Coverage Requirements

| Scope | Target |
|-------|--------|
| Core logic | >= 90% |
| Public APIs | 100% |

## Validation Commands

| Task | Command |
|------|---------|
| Run all tests | `uv run pytest` |
| Run tests with coverage | `uv run pytest --cov` |
| Run specific test file | `uv run pytest tests/path/to/test_module.py` |
| Run specific test function | `uv run pytest tests/path/to/test_module.py::test_function_name` |
| Run tests matching pattern | `uv run pytest -k "pattern"` |
| Run tests with verbose output | `uv run pytest -v` |
| Run tests and stop on first failure | `uv run pytest -x` |
| Show local variables in tracebacks | `uv run pytest -l` |
