# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Structure

```
src/chain_reaction/   # Library tools and classes
agents/               # LangSmith Studio agent definitions (langgraph.json)
notebooks/            # Learning notebooks by topic
mcp-servers/          # FastMCP server implementations
```

## Quick Reference

- Install/sync dependencies: `uv sync`
- Format code: `ruff format`
- Lint code: `ruff check`
- Type check: `ty check`
- Run tests: `uv run pytest`

## Development Convention Skills

Development conventions are provided through **skills** that are automatically loaded when relevant.

| Skill | Purpose |
|-------|---------|
| `frameworks` | Approved frameworks and Context7 IDs for documentation |
| `code-organization` | Module structure, imports, file layouts |
| `naming-conventions` | Function, class, variable naming patterns |
| `function-design` | Function signatures, parameters, return types |
| `class-design` | Class design, composition, inheritance |
| `data-structures` | Pydantic models vs dataclasses |
| `type-hints` | Type annotations, generics, protocols |
| `pythonic-conventions` | Comprehensions, built-ins, context managers, unpacking |
| `docstring-conventions` | Google-style docstrings |
| `testing` | Pytest conventions, fixtures, parametrization |

## Claude-Specific Rules

**IMPORTANT: YOU MUST follow these rules:**

1. **Use designated frameworks ONLY** - Use the `frameworks` skill to check approved libraries. NEVER substitute alternatives.
2. **Apply relevant skills** - Skills provide all coding standards for this repository.
3. **Fetch docs when uncertain** - Use Context7 MCP to search library/API documentation. NEVER assume API details.
4. **Use sub-agents for specialized tasks:**
   - `planner` - Creating implementation plans (use `/plan` command)
   - `python-code-writer` - Writing clean, maintainable, testable code
   - `python-test-writer` - Creating/updating pytest tests
   - `python-code-reviewer` - Code review after significant changes
5. **NEVER hallucinate** - Only use verified packages. Ask if uncertain about paths, modules, or APIs.
6. **NEVER delete code** unless explicitly instructed or specified in `TASK.md`.
7. **NEVER commit changes** unless explicitly instructed or specified in `TASK.md`.

## Slash Commands

Reusable workflows in `.claude/commands/`:

- `/plan <description>` - Create comprehensive implementation plan before coding
- `/project:implement Phase <N> from <plan-document-path>` - Implement one or more phases from a coding plan
- `/review <target>` - Code review (files, `--commit`, `--staged`, optionally with `--plan` context)
- `/update-plan <plan-path>` - Sync with main and update plan to reflect completed phases and changes
- `/pr-description` - Generate PR description from branch changes (optionally with `--plan` and `--phases` context)
