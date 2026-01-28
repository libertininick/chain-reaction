# Documentation

**All public functions/classes/modules MUST have Google-style docstrings.**

## Docstring Guidelines

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
    """
```

## When to Use Comments vs Docstrings

| Type | Use For |
|------|---------|
| Docstrings | Public API documentation (functions, classes, modules) |
| Comments | Explain *why* for non-obvious implementation details |

```python
# Use binary search here because the list is sorted and can have 100k+ items
index = bisect.bisect_left(sorted_items, target)
```

## Module Docstrings

Each module should have a docstring describing its purpose:

```python
"""Embedding utilities for vector similarity search.

This module provides functions for creating, comparing, and manipulating
embeddings used in semantic search and retrieval systems.
"""
```
