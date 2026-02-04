# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Structure

```
src/chain_reaction/   # Library tools and classes
agents/               # LangSmith Studio agent definitions
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
| Run tests | `uv run pytest` |
| Run tests with coverage | `uv run pytest --cov` |

## Critical Rules

> **PYTHON EXECUTION**: When running generated Python via Bash, use `run-python-safely` skill first.
> Exceptions: `uv run pytest`, `ruff`, `ty check`, other standard CLI tools.

1. **Approved frameworks only** - Use `frameworks` skill; never substitute alternatives
2. **Apply convention skills** - Skills provide coding standards
3. **Fetch docs when uncertain** - Use Context7 MCP (see `frameworks` skill for IDs)
4. **Use specialized agents** - See Agents section
5. **Never hallucinate** - Ask if uncertain about paths, modules, or APIs
6. **Never delete code** unless explicitly instructed
7. **Never commit** unless explicitly instructed

---

## Commands

Reusable workflows in `.claude/commands/`. See each file for details.

| Command | Purpose |
|---------|---------|
| `/plan` | Create implementation plan |
| `/implement` | Execute plan phases |
| `/review` | Code review |
| `/update-plan` | Sync plan with main |
| `/pr-description` | Generate PR description |

---

## Agents

Specialized sub-agents in `.claude/agents/`. See each file for details.

| Agent | Scope | Model |
|-------|-------|-------|
| `planner` | Creates implementation plans | Opus |
| `python-code-writer` | Writes production code | Opus |
| `python-test-writer` | Writes tests | Opus |
| `code-style-reviewer` | Reviews style/conventions | Sonnet |
| `code-substance-reviewer` | Reviews design/correctness | Opus |

### Workflow

```
/plan → /implement → /review → /pr-description
```

---

## Skills

Skills provide coding standards and conventions. See `.claude/skills/manifest.json` for the complete catalog.

**Categories**:
- **Conventions**: `frameworks`, `naming-conventions`, `function-design`, `class-design`, `data-structures`, `type-hints`, `pythonic-conventions`, `docstring-conventions`, `code-organization`, `testing`, `complexity-refactoring`
- **Assessment**: `maintainability`, `testability`
- **Templates**: `plan-template`, `review-template`, `pr-description-template`
- **Utilities**: `run-python-safely`, `write-markdown-output`, `create-skill`

---

## Agent Outputs

Agents write outputs to `.claude/agent-outputs/` using `write-markdown-output` skill:

```
.claude/agent-outputs/
├── plans/           # Implementation plans
├── reviews/         # Code reviews
└── pr-descriptions/ # PR descriptions
```
