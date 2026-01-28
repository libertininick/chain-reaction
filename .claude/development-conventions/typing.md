# Type Safety

**Type annotations are REQUIRED on all functions and classes.**

## Modern Type Hints (Python 3.10+)

```python
# Use union syntax, not Optional
def get_user(user_id: int) -> User | None: ...

# Use lowercase builtins for generics
def process(items: list[str]) -> dict[str, int]: ...

# Use collections.abc for abstract container types
from collections.abc import Sequence, Mapping, Callable, Iterator, Iterable

def transform(items: Sequence[str]) -> Mapping[str, int]: ...

def apply(fn: Callable[[int], str], values: Iterable[int]) -> Iterator[str]: ...
```

## Generic Types

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

## Self Type (Python 3.11+)

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

## Protocol for Structural Subtyping

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

## Type Aliases

```python
from typing import TypeAlias

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
Embedding: TypeAlias = list[float]
BatchEmbeddings: TypeAlias = list[Embedding]

def encode(texts: list[str]) -> BatchEmbeddings: ...
```

## TypedDict for JSON-like Structures

```python
from typing import TypedDict, Required, NotRequired

class UserResponse(TypedDict):
    id: Required[int]
    name: Required[str]
    email: NotRequired[str]

def parse_user(data: dict[str, Any]) -> UserResponse: ...
```

## Literal Types for Constrained Strings

```python
from typing import Literal

Status = Literal["pending", "active", "completed", "failed"]

def update_status(task_id: int, status: Status) -> None: ...
```

## Guidelines

| Rule | Guidance |
|------|----------|
| Prefer `X \| None` | Over `Optional[X]` for clarity |
| Use `Sequence` | Over `list` in parameters when you only need iteration |
| Use `Mapping` | Over `dict` in parameters when you only need read access |
| Return concrete types | Return `list`, `dict` but accept `Sequence`, `Mapping` |
| Use `Any` sparingly | Acceptable at system boundaries (JSON parsing, plugin systems) |
| Use `TypedDict` | For typed dictionary structures, especially API responses |
| Use `Literal` | For constrained string values |
