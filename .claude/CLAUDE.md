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

| Task | Command |
|------|---------|
| Install/sync dependencies | `uv sync` |
| Format code | `uv run ruff format` |
| Lint code | `uv run ruff check` |
| Docstring check | `uv tool run pydoclint --style=google --allow-init-docstring=True` |
| Type check | `uv run ty check` |
| Run all tests | `uv run pytest` |
| Run specific test file | `uv run pytest tests/path/test_file.py` |
| Run specific test | `uv run pytest tests/path/test_file.py::test_name` |

## Claude-Specific Rules

> **CRITICAL: PYTHON EXECUTION RULE**
>
> When running Python code via Bash (e.g., `python -c "..."` or `python script.py`), you **MUST** use the `run-python-safely` skill FIRST. Do NOT run Python directly.
>
> **Correct workflow:**
> 1. Invoke `Skill(skill="run-python-safely")`
> 2. Use the command from the skill: `uv run python .claude/skills/run-python-safely/scripts/run_python_safely.py -c "your code"`
>
> **Exceptions (skip the skill for these):**
> - `uv run pytest` - running tests
> - `ruff`, `ty check`, `mypy` - linting/type checking
> - Other standard CLI tools

**IMPORTANT: YOU MUST follow these rules:**

1. **Use designated frameworks ONLY** - Use the `frameworks` skill to check approved libraries. NEVER substitute alternatives.
2. **Apply relevant skills** - Skills provide all coding standards for this repository.
3. **Fetch docs when uncertain** - Use Context7 MCP to search library/API documentation. NEVER assume API details.
4. **Use specialized agents** - See Agents section below for when to use each agent.
5. **NEVER hallucinate** - Only use verified packages. Ask if uncertain about paths, modules, or APIs.
6. **NEVER delete code** unless explicitly instructed or specified in `TASK.md`.
7. **NEVER commit changes** unless explicitly instructed or specified in `TASK.md`.

---

## Slash Commands

Reusable workflows in `.claude/commands/`:

| Command | Purpose |
|---------|---------|
| `/plan <description>` | Create comprehensive implementation plan before coding |
| `/implement Phase <N> from <plan-path>` | Implement one or more phases from a coding plan |
| `/review <target>` | Code review (files, `--commit`, `--staged`, optionally with `--plan` context) |
| `/update-plan <plan-path>` | Sync with main and update plan to reflect completed phases |
| `/pr-description` | Generate PR description from branch changes (optionally with `--plan` and `--phases` context) |

### Command Examples

```bash
# Planning
/plan add SQL query validation for dataframe toolkit

# Implementation
/implement Phase 1 from .claude/agent-outputs/plans/2024-01-22T143052Z-sql-validation-plan.md
/implement Phase 2 and 3 from .claude/agent-outputs/plans/2024-01-22T143052Z-sql-validation-plan.md

# Code Review
/review src/chain_reaction/tools/parser.py
/review --staged
/review --commit abc123f
/review --commits main..HEAD
/review --staged --plan .claude/agent-outputs/plans/2024-01-22T143052Z-sql-validation-plan.md --phase 2

# Plan Updates
/update-plan .claude/agent-outputs/plans/2024-01-22T143052Z-sql-validation-plan.md

# PR Description
/pr-description
/pr-description --plan .claude/agent-outputs/plans/2024-01-22T143052Z-sql-validation-plan.md --phases 1,2
```

---

## Specialized Agents

Use specialized agents for specific tasks. Each agent has defined responsibilities and tools.

### Planning

| Agent | When to Use | Model |
|-------|-------------|-------|
| `planner` | Creating implementation plans for features, refactoring, or complex bug fixes. Invoke via `/plan` command. | Opus |

### Implementation

| Agent | When to Use | Model |
|-------|-------------|-------|
| `python-code-writer` | Writing new features, functions, classes, or modules. Does NOT write tests. | Opus |
| `python-test-writer` | Creating/updating pytest tests. Always run tests after writing. | Opus |

### Code Review

| Agent | When to Use | Model |
|-------|-------------|-------|
| `code-style-reviewer` | Style, conventions, organization (invoked by `/review` command) | Sonnet |
| `code-substance-reviewer` | Correctness, design, maintainability (invoked by `/review` command) | Opus |

The `/review` command orchestrates these agents sequentially (style first, then substance), then aggregates findings into a unified report.

### Agent Workflow

```
/plan → planner agent
    ↓
/implement → python-code-writer + python-test-writer
    ↓
/review → code-style-reviewer (first)
        → code-substance-reviewer (second)
        → aggregates into unified report
    ↓
/pr-description → generates PR summary
```

---

## Skills

Skills provide coding standards and conventions. They are automatically loaded when relevant, or can be invoked explicitly.

### Coding Convention Skills

These skills define how code should be written in this repository.

| Skill | Purpose | Auto-loads When |
|-------|---------|-----------------|
| `frameworks` | Approved frameworks and Context7 IDs | Checking/using external libraries |
| `code-organization` | Module structure, imports, file layouts | Creating/modifying modules |
| `naming-conventions` | Function, class, variable naming patterns | Writing new code elements |
| `function-design` | Function signatures, parameters, return types | Writing functions |
| `class-design` | Class design, composition, inheritance | Writing classes |
| `data-structures` | Pydantic models vs dataclasses | Creating data containers |
| `type-hints` | Type annotations, generics, protocols | Adding type hints |
| `pythonic-conventions` | Comprehensions, built-ins, context managers | Writing Python code |
| `docstring-conventions` | Google-style docstrings | Documenting public APIs |
| `testing` | Pytest conventions, fixtures, parametrization | Writing tests |
| `complexity-refactoring` | Extracting helper functions | When C901 limit exceeded |

### Review Assessment Skills

Used by code reviewers to assess code quality.

| Skill | Purpose | Used By |
|-------|---------|---------|
| `maintainability` | Readability, change tolerance, hidden assumptions, debuggability | `code-substance-reviewer` |
| `testability` | Dependency injection, global state, pure functions, test seams | `code-substance-reviewer` |

### Template Skills

Provide format specifications for agent outputs.

| Skill | Purpose | Used By |
|-------|---------|---------|
| `plan-template` | Implementation plan format and examples | `/plan` command |
| `review-template` | Code review format and severity guidance | `/review` command |
| `pr-description-template` | PR description format and examples | `/pr-description` command |

### Utility Skills

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `run-python-safely` | Execute Python code safely via AST analysis before running | **MANDATORY** when agents execute Python code they've generated (exceptions: `uv run pytest`, standard CLI tools) |
| `write-markdown-output` | Write timestamped markdown files to agent output directories | When agents write plans, reviews, or PR descriptions |
| `create-skill` | Create new Claude Code skills | When converting conventions or workflows into skills |

---

## Agent Output Locations

Agents save their outputs to structured directories using the `write-markdown-output` skill:

```
.claude/agent-outputs/
├── plans/                  # Implementation plans
│   └── <timestamp>-<scope>-plan.md
├── reviews/                # Code reviews
│   └── <timestamp>-<scope>-review.md
└── pr-descriptions/        # PR descriptions
    └── <timestamp>-<branch>-pr.md
```

Timestamp format: `YYYY-MM-DDTHHmmssZ` (UTC ISO format)

**Usage**: Agents use the skill to write output files:
```bash
uv run python .claude/skills/write-markdown-output/scripts/write_markdown_output.py \
    -s "<scope>" \
    -c "<content>" \
    -o ".claude/agent-outputs/<type>"
```

---

## Typical Workflows

### New Feature Implementation

1. **Plan**: `/plan <feature description>`
2. **Review plan**: Iterate until approved
3. **Implement**: `/implement Phase 1 from <plan-path>`
4. **Review**: `/review --staged --plan <plan-path> --phase 1`
5. **Repeat** for each phase
6. **PR**: `/pr-description --plan <plan-path> --phases 1,2,3`

### Bug Fix

1. **Simple fix**: Fix directly, no plan needed
2. **Complex fix**: Use `/plan` first, then `/implement`
3. **Review**: `/review --staged`

### Code Review Only

```bash
/review src/chain_reaction/module.py           # Single file
/review src/chain_reaction/tools/              # Directory
/review --staged                               # Staged changes
/review --commit HEAD                          # Last commit
/review --commits main..HEAD                   # All branch changes
```

---

## Context7 MCP Integration

Use Context7 to fetch documentation for approved frameworks:

1. Check `frameworks` skill for the library's Context7 ID
2. Use `mcp__context7__query-docs` with the Context7 ID
3. Query specific APIs or patterns you need

Example:
```
# From frameworks skill, LangGraph has ID: /langchain-ai/langgraph
mcp__context7__query-docs(libraryId="/langchain-ai/langgraph", query="how to create a graph with conditional edges")
```

---

## Validation Commands

Run these before completing work:

```bash
uv run ruff format .                                              # Format code
uv run ruff check .                                               # Lint code
uv run ruff check --select C901                                   # Check function complexity
uv tool run pydoclint --style=google --allow-init-docstring=True  # Docstring check
uv run ty check                                                   # Type check
uv run pytest                                                     # Run tests
uv run pytest --cov                                               # Run tests with coverage
```
