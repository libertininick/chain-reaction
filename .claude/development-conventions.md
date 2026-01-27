# Development Conventions

## Code Organization

- Organize code into clearly separated modules, grouped by feature or responsibility
- Use consistent naming conventions, file structure, and architecture patterns
- Use composition over inheritance
- Follow DRY, but NEVER create tight coupling just to avoid repetition

## Type Safety

**IMPORTANT: Type annotations are REQUIRED on all functions and classes.**

```python
# Good
def process_data(items: list[str], threshold: float = 0.5) -> dict[str, int]:
    ...

# Bad - missing type hints
def process_data(items, threshold=0.5):
    ...
```

Validate with: `uv run ty check .`

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


# Bad - raw dictionary with no validation or documentation
def search(query: str) -> list[dict]:
    ...

# Usage - error-prone string keys, no autocompletion
results = search("python async")
for result in results:
    print(f"{result['doc_id']}: {result['score']:.2f}")  # KeyError: 'doc_id'
```

Use **Pydantic** when you need validation, serialization, or API boundaries.
Use **dataclasses** for simple internal data containers.

## Documentation

**All public functions/classes/modules MUST have Google-style docstrings.**

- Explain the **why**, not the how
- Include example usage when helpful (tested by doctest)
- Validate with: `uv tool run pydoclint --style=google --allow-init-docstring=True`

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

    Example:
        >>> calculate_similarity([1.0, 0.0], [1.0, 0.0])
        1.0
    """
```

## Error Handling

**Fail fast with clear, actionable error messages.**

```python
# Good - clear context for debugging
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Set it with: export OPENAI_API_KEY='sk-...'")

# Bad - vague error
if not api_key:
    raise ValueError("Invalid configuration")
```

## Code Quality Principles

| Principle | Guidance |
|-----------|----------|
| Simplicity | Prioritize readable code. NEVER over-engineer. |
| PEP 8 | Follow strictly. Format with `ruff format`. |
| Naming | Use descriptive, consistent names for functions, classes, variables. |
| Testing | Aim for >=90% coverage. Test after any logic change. |

## Anti-Patterns to Avoid

- NEVER use inheritance when composition works
- NEVER create abstractions for single-use cases
- NEVER add "just in case" features or parameters
- NEVER leave commented-out code in production