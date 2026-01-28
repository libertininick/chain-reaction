# Function Design

## Core Principles

### Explicit is Better Than Implicit

Function purpose, arguments, and behavior should be clear from the signature and name. Avoid hidden dependencies, global state, or surprising side effects.

```python
# Bad - hidden dependency on global state
_current_user: User | None = None

def get_permissions() -> list[str]:
    return _current_user.permissions  # What user? Where is this set?

# Good - explicit dependency
def get_permissions(user: User) -> list[str]:
    return user.permissions
```

### Single Responsibility Principle (SRP)

Functions should do one thing and do it well. If a function name contains "and" or you need multiple paragraphs to describe it, split it.

```python
# Bad - does two things
def validate_and_save_user(user: User) -> bool:
    if not user.email or "@" not in user.email:
        return False
    db.save(user)
    return True

# Good - separate concerns
def is_valid_email(email: str) -> bool:
    return bool(email and "@" in email)

def save_user(user: User) -> None:
    if not is_valid_email(user.email):
        raise ValidationError("Invalid email address")
    db.save(user)
```

### Pure Functions When Possible

Prefer functions that return new values rather than modifying inputs. Pure functions are easier to test, reason about, and compose.

```python
# Bad - modifies input
def normalize_scores(scores: list[float]) -> None:
    max_score = max(scores)
    for i in range(len(scores)):
        scores[i] /= max_score

# Good - returns new value
def normalize_scores(scores: list[float]) -> list[float]:
    max_score = max(scores)
    return [s / max_score for s in scores]
```

### Return Early with Guard Clauses

Validate preconditions at the top of the function and return/raise immediately. This reduces nesting and keeps the happy path at the base indentation level.

```python
# Bad - deeply nested
def process_order(order: Order | None) -> Receipt:
    if order is not None:
        if order.items:
            if order.payment_verified:
                return generate_receipt(order)
            else:
                raise PaymentError("Payment not verified")
        else:
            raise ValidationError("Order has no items")
    else:
        raise ValidationError("Order is required")

# Good - guard clauses
def process_order(order: Order | None) -> Receipt:
    if order is None:
        raise ValidationError("Order is required")
    if not order.items:
        raise ValidationError("Order has no items")
    if not order.payment_verified:
        raise PaymentError("Payment not verified")

    return generate_receipt(order)
```

### Return Type Stability

Functions should return the same type regardless of input. This makes functions predictable and easier to compose.

```python
# Bad - inconsistent return types
def find_user(user_id: int) -> User | None | bool:
    if user_id < 0:
        return False  # Why boolean?
    user = db.get(user_id)
    return user  # Returns User or None

# Good - consistent return type
def find_user(user_id: int) -> User:
    if user_id < 0:
        raise ValueError("user_id must be >=0; got {user_id}")
    return db.get(user_id)
```

### Prefer Exceptions to Returning None for Errors

When a function cannot complete its intended purpose, raise an exception rather than returning `None`. Reserve `None` for "no result found" cases, not errors.

```python
# Bad - None conflates "not found" with "error"
def load_config(path: Path) -> Config | None:
    if not path.exists():
        return None  # Is this "not found" or "error"?
    try:
        return Config.from_file(path)
    except ParseError:
        return None  # Same return for different problems

# Good - exceptions for errors, None only for "not found"
def load_config(path: Path) -> Config:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    try:
        return Config.from_file(path)
    except ParseError as e:
        raise ConfigurationError(f"Invalid config format: {e}") from e
```

### Command-Query Separation

Functions should either perform an action (command) OR return data (query), not both. This makes behavior predictable.

```python
# Bad - does both
def get_next_id() -> int:
    global _counter
    _counter += 1  # Side effect (command)
    return _counter  # Returns value (query)

# Good - separate command and query
class IdGenerator:
    def __init__(self) -> None:
        self._counter = 0

    def next(self) -> int:
        """Return the next ID (query only)."""
        return self._counter + 1

    def advance(self) -> None:
        """Increment the counter (command only)."""
        self._counter += 1

    def take(self) -> int:
        """Get next ID and advance. Clearly named to indicate both operations."""
        id = self.next()
        self.advance()
        return id
```

### Keep Functions Small and Focused

Functions should be short enough to understand at a glance. If a function requires scrolling or extensive comments to understand, consider splitting it.

```python
# Bad - too much happening
def process_document(doc: Document) -> ProcessedDocument:
    # Validate
    if not doc.content:
        raise ValueError("Empty document")
    if len(doc.content) > MAX_LENGTH:
        raise ValueError("Document too long")
    # Extract metadata
    title = doc.content.split("\n")[0]
    word_count = len(doc.content.split())
    # Transform content
    cleaned = doc.content.lower().strip()
    tokens = cleaned.split()
    # ... 50 more lines

# Good - composed of focused functions
def process_document(doc: Document) -> ProcessedDocument:
    validate_document(doc)
    metadata = extract_metadata(doc)
    tokens = tokenize_content(doc.content)
    return ProcessedDocument(metadata=metadata, tokens=tokens)
```

---

## Parameter Guidelines

### Limit Positional Parameters

Prefer fewer positional parameters. Use dataclasses or Pydantic models for functions that need many related inputs.

```python
# Bad - too many positional parameters
def create_user(name: str, email: str, age: int, role: str, dept: str) -> User: ...

# Good - group related parameters
@dataclass
class UserInput:
    name: str
    email: str
    age: int
    role: str
    department: str

def create_user(input: UserInput) -> User: ...
```

### Use Keyword-Only Arguments

ALWAYS use `*` to force keyword arguments for any parameter with a default value, or when a function has more than 2-3 parameters.

```python
def fetch_data(
    url: str,
    *,  # Everything after this must be keyword-only
    timeout: float = 30.0,
    retries: int = 3,
    headers: dict[str, str] | None = None,
) -> Response:
    """Fetch data from URL with retry logic."""
    ...

# Callers must be explicit
response = fetch_data("https://api.example.com", timeout=60.0, retries=5)
```

### Never Use Mutable Default Arguments

Mutable defaults (lists, dicts, sets) are created once and shared across all calls. Always use `None` and create the mutable inside the function.

```python
# Bad - mutable default (created once, shared across calls!)
def add_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

add_item("a")  # Returns ["a"]
add_item("b")  # Returns ["a", "b"] - BUG! List persists between calls

# Good - None default with internal creation
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

---

## Async Functions

Prefix async functions with `async_` to make the async nature visible at call sites.

```python
# Good - async prefix makes it clear
async def async_fetch_user(user_id: int) -> User:
    return await client.get(f"/users/{user_id}")

async def async_process_batch(items: list[Item]) -> list[Result]:
    return await asyncio.gather(*[async_process(item) for item in items])

# Usage is clear about async nature
user = await async_fetch_user(123)
```
