# Testing Conventions

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

Pattern: `test_<function>_<scenario>_<expected_result>`

```python
def test_calculate_similarity_identical_vectors_returns_one() -> None:
    """Identical vectors should have similarity of 1.0."""
    vec = [1.0, 0.0, 0.0]
    assert calculate_similarity(vec, vec) == 1.0


def test_calculate_similarity_mismatched_dimensions_raises_value_error() -> None:
    """Vectors with different dimensions should raise ValueError."""
    with pytest.raises(ValueError, match="dimension"):
        calculate_similarity([1.0, 0.0], [1.0, 0.0, 0.0])
```

## Test Structure: Arrange-Act-Assert

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

## Fixtures

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

## Parametrized Tests

Use for testing multiple inputs:

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

## Coverage Requirements

- Aim for >=90% coverage on core logic
- 100% coverage on public APIs

## Example: Test Class with Fixtures

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
