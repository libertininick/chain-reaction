# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Quick Reference

- `uv sync` - Install dependencies
- `uv run pytest` - Run tests
- `uv run pytest tests/test_<file>.py::test_<name>` - Run specific test
- `uv run ruff check --fix && uv run ruff format` - Format code
- `uv run ty check .` - Type check
- `uv tool run pydoclint --style=google --allow-init-docstring=True src/ tests/` - Check docstring format

## Project Structure

```
src/chain_reaction/   # Library tools and classes
agents/               # LangSmith Studio agent definitions (langgraph.json)
notebooks/            # Learning notebooks by topic
mcp-servers/          # FastMCP server implementations
```

## Critical Rules

**IMPORTANT: YOU MUST follow these rules:**

1. **Use designated frameworks ONLY** - See [frameworks.md](frameworks.md). NEVER substitute alternatives (e.g., no pandas, use polars).
2. **Always adhere to explicit conventions** - See [development-conventions.md](development-conventions.md).
3. **Fetch docs when you are uncertain** - NEVER assume API details, if you are uncertain use Context7 MCP to search library/API documentation without me having to explicitly ask.
4. **Use sub-agents for specialized tasks:**
   - `python-test-writer` - Creating/updating pytest tests
   - `python-code-reviewer` - Code review after significant changes
5. **NEVER hallucinate** - Only use verified packages. Ask if uncertain about paths, modules, or APIs.
6. **NEVER delete code** unless explicitly instructed or specified in `TASK.md`.
7. **NEVER commit changes** unless explicitly instructed or specified in `TASK.md`.


## Conventions & Standards

See [development-conventions.md](development-conventions.md) for:
- Code organization and naming
- Type hints and docstrings (Google-style, explain "why" not "how")
- Error handling (fail fast with clear messages)

See [frameworks.md](frameworks.md) for:
- Approved frameworks and their purposes
- Documentation links for each framework
- When to fetch documentation

## Slash Commands

Reusable workflows in `.claude/commands/`:

- `/project:implement-and-review <description>` - Implement a new feature and review
