# Development Conventions

## Guiding Principles

| Principle | Guidance |
|-----------|----------|
| No Broken Windows | Fix lint errors before committing. Address TODO comments promptly. Remove unused code. |
| Simplicity | Prioritize straightforward, readable code. Avoid over-engineering. |
| Explicitness | Avoid magic. Be explicit about types, defaults, and behavior. |
| Pure Functions | Functions should take inputs and return new outputs without modifying external state. |
| Composition Over Inheritance | Assemble behavior from small components rather than deep class hierarchies. |
| High Cohesion & Low Coupling | Group related functionality; minimize dependencies between modules. |
| PEP 8 | Follow strictly. Format with `ruff format`. |

## Anti-Patterns to Avoid

These cause subtle bugs or maintenance issues:

| Anti-Pattern | Why It's Bad |
|--------------|--------------|
| Commented-out code | Creates confusion; use version control instead |
| Implicit dependencies | Makes code hard to test; use explicit injection |
| Premature abstraction | Three similar lines > one premature abstraction |
| Speculative features | Only implement what's needed now (YAGNI) |
| Overly broad `except:` | Obscures real errors; catch specific exceptions |
| Returning dictionaries or tuples | Use structured data classes instead |
| Coverage-driven tests | Test meaningful behavior, not lines to meet coverage threshold |

## Detailed Guides

| Document | Topics |
|----------|--------|
| [organization.md](organization.md) | Code organization, module design, imports |
| [patterns.md](patterns.md) | Composition, error handling, Pythonic idioms |
| [naming.md](naming.md) | Naming conventions with examples |
| [functions.md](functions.md) | Function design, parameters, early returns |
| [data-structures.md](data-structures.md) | Pydantic models and dataclasses |
| [typing.md](typing.md) | Type hints, generics, protocols |
| [testing.md](testing.md) | Test organization, fixtures, parametrization |
| [documentation.md](documentation.md) | Docstrings and comments |

## Validation Commands

```bash
uv run ruff check --fix && uv run ruff format   # Lint and format
uv run ty check .                               # Type check
uv run pytest --cov --cov-fail-under=90         # Tests with coverage
uv tool run pydoclint --style=google --allow-init-docstring=True src/ tests/
```
