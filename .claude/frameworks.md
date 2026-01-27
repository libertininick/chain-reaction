# Frameworks

## Critical Rules

1. **Use ONLY these frameworks. NEVER introduce alternatives or substitutes.**

2. **Fetch docs when you are uncertain** - NEVER assume API details, if you are uncertain use Context7 MCP to search library/API documentation without me having to explicitly ask. Use the Context7 ID directly (if available) to retrieve framework documentation. That way, Context7 MCP server can skip the library-matching step and directly continue with retrieving docs:

```sh
# Example: If uncertain about Pydantic validation syntax
# Use: mcp__context7__query-docs with libraryId=/pydantic/pydantic
```

3. **Use modern patterns** - Avoid deprecated methods. If uncertain, check latest framework documentation for current idioms.

## Approved Frameworks

### LangChain

- **Purpose**: LangChain provides a pre-built agent architecture and model integrations to help you get started quickly and seamlessly incorporate LLMs into your agents and applications. If you want a higher-level abstraction, we recommend you use LangChain’s agents that provide pre-built architectures for common LLM and tool-calling loops.
- **Docs**: https://docs.langchain.com/oss/python/langchain/overview
- **Context7 ID**: /websites/langchain

### LangGraph

- **Purpose**: LangGraph is a low-level orchestration framework and runtime for building, managing, and deploying long-running, stateful agents. Use LangGraph when you have more advanced needs that require a combination of deterministic and agentic workflows, heavy customization, and carefully controlled latency.
- **Docs**: https://docs.langchain.com/oss/python/langgraph/overview
- **Context7 ID**: /websites/langgraph

### FastMCP

- **Purpose**: MCP server implementations
- **Docs**: https://gofastmcp.com/getting-started/welcome
- **Context7 ID**: /jlowin/fastmcp

### Polars

- **Purpose**: DataFrame operations
- **Docs**: https://docs.pola.rs/api/python/stable/reference/index.html
- **Context7 ID**: /pola-rs/polars

### Pydantic

- **Purpose**: Data validation, settings
- **Docs**: https://docs.pydantic.dev/latest
- **Context7 ID**: /pydantic/pydantic

### diskcache

- **Purpose**: Disk-based caching
- **Docs**: https://grantjenks.com/docs/diskcache/
- **Context7 ID**: /grantjenks/python-diskcache

### loguru

- **Purpose**: Logging
- **Docs**: https://loguru.readthedocs.io/en/stable/
- **Context7 ID**: /delgan/loguru

### pytest

- **Purpose**: Testing
- **Docs**: https://docs.pytest.org/en/stable/
- **Context7 ID**: /pytest-dev/pytest

### pytest-check

- **Purpose**: A pytest plugin that allows multiple failures per test
- **Docs**: https://github.com/okken/pytest-check
- **Context7 ID**: /okken/pytest-check

### ruff

- **Purpose**: Linter and formatter
- **Docs**: https://docs.astral.sh/ruff/
- **Context7 ID**: /astral-sh/ruff

### sqlglot

- **Purpose**: SQLGlot is a no-dependency SQL parser, transpiler, optimizer, and engine. It can be used to format SQL or translate between 31 different dialects like DuckDB, Presto / Trino, Spark / Databricks, Snowflake, and BigQuery. SQLGlot can detect a variety of syntax errors, such as unbalanced parentheses, incorrect usage of reserved keywords, and so on. 
- **Docs**: https://sqlglot.com/sqlglot.html
- **Context7 ID**: /tobymao/sqlglot

### ty

- **Purpose**: Type checker
- **Docs**: https://docs.astral.sh/ty/
- **Context7 ID**: /astral-sh/ty

### uv

- **Purpose**: Package manager
- **Docs**: https://docs.astral.sh/uv/
- **Context7 ID**: /astral-sh/uv



