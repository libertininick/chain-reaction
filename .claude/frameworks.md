# Frameworks

**IMPORTANT: Use ONLY these frameworks. NEVER introduce alternatives or substitutes.**

## Approved Frameworks

| Framework | Purpose | Docs |
|-----------|---------|------|
| LangChain | LLM orchestration, chains, prompts | [docs](https://docs.langchain.com/oss/python/langchain/overview) |
| LangGraph | Stateful agent workflows | [docs](https://docs.langchain.com/oss/python/langgraph/overview) |
| FastMCP | MCP server implementations | [docs](https://gofastmcp.com/getting-started/welcome) |
| Polars | DataFrame operations | [docs](https://docs.pola.rs/) |
| Pydantic | Data validation, settings | [docs](https://docs.pydantic.dev/latest) |
| diskcache | Disk-based caching | [docs](https://grantjenks.com/docs/diskcache/) |
| loguru | Logging | [docs](https://loguru.readthedocs.io/en/stable/) |
| pytest | Testing | [docs](https://docs.pytest.org/en/stable/) |
| ruff | Linter and formatter | [docs](https://docs.astral.sh/ruff/) |
| ty | Type checker | [docs](https://docs.astral.sh/ty/) |
| uv | Package manager | [docs](https://docs.astral.sh/uv/) |

## Critical Rules

1. **NEVER substitute frameworks** - No pandas (use polars), no pickle (use diskcache), no print (use loguru)
2. **ALWAYS fetch docs first** - Use WebFetch before writing framework code. NEVER assume APIs.
3. **Use modern patterns** - Avoid deprecated methods. Check docs for current idioms.

## Framework Patterns

### Pydantic
```python
# Good - define structured inputs and return values for functions
from pydantic import BaseModel, Field

class UserInfo(BaseModel):
    """Information about a user."""
    name: str = Field(description="User name.")
    age: float = Filed(description="User age. Must be > 0", gt=0)
    likes: list[str] = Field(description="A list of user's likes", default_factory=list)

def get_user_info(...) -> UserInfo:
    """Fetch user information."""
    ...

# Bad - using Python dictionaries or tuples for structured info 
def get_user_info(...) -> dict:
    """Fetch user information."""
    ...
```

### Polars
```python
# Good - use expressions and lazy evaluation
df = pl.scan_csv("data.csv").filter(pl.col("value") > 0).collect()

# Bad - pandas patterns
df = df[df["value"] > 0]  # Use pl.col() expressions
```


## When to Fetch Documentation

**YOU MUST use WebFetch** when:
- Implementing new features with any framework
- Uncertain about method signatures or parameters
- Writing code that integrates multiple frameworks
- Using framework features not yet used in this conversation