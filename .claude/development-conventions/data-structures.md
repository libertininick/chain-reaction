# Data Structures

**Use Pydantic models or dataclasses instead of raw dictionaries or tuples.**

Structured data classes provide:
- **IDE support**: Autocompletion, refactoring, go-to-definition
- **Validation**: Automatic type checking (Pydantic)
- **Documentation**: Self-documenting field names and types
- **Immutability**: Prevent mutations with `frozen=True`

## When to Use Each

| Use Case | Choice |
|----------|--------|
| Validation, serialization, API boundaries | Pydantic `BaseModel` |
| Simple internal data containers | `dataclass` |
| Immutable value objects, hashable keys | `dataclass(frozen=True)` |
| Lightweight tuple replacement | `dataclass` |
| Performance-critical hot paths | `dataclass` (lower overhead than Pydantic) |

Avoid returning python dictionaries or functions, and NEVER use `NamedTuple` unless you are refactoring a function that returned a tuple but must retain backward compatibility.

## Pydantic Models

```python
from pydantic import BaseModel, Field

class SearchResult(BaseModel):
    """A single search result from the retrieval system."""

    document_id: str = Field(description="Unique identifier for the document")
    content: str = Field(description="The matched text content")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score")
    metadata: dict[str, str] = Field(default_factory=dict)
```

## Configuration with Pydantic Settings

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

## Dataclasses

```python
from dataclasses import dataclass

@dataclass
class Point:
    """A 2D point."""
    x: float
    y: float

@dataclass(frozen=True)
class UserId:
    """Immutable user identifier, safe for use as dict key."""
    value: int
```
