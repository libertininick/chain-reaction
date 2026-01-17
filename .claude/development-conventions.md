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

## Documentation

**All public functions/classes/modules MUST have Google-style docstrings.**

- Explain the **why**, not the how
- Include example usage when helpful (tested by doctest)
- Validate with: `uv run pydoclint`

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