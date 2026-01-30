---
name: create-skill
description: Create a new Claude Code skill. Use when converting conventions, workflows, or knowledge into actionable skills.
argument-hint: <skill-name> [source-file]
---

# Create a Claude Code Skill

Create skills that extend Claude's capabilities with actionable, prescriptive instructions.

**Documentation**: https://code.claude.com/docs/en/skills

## Skill Location

```
.claude/skills/<skill-name>/SKILL.md
```

## SKILL.md Structure

```yaml
---
name: skill-name
description: What this skill does. Claude uses this to decide when to load it.
user-invocable: true          # Set false to hide from /menu (reference content)
disable-model-invocation: true # Set true to prevent auto-loading (manual only)
argument-hint: [arg1] [arg2]  # Shown during autocomplete
allowed-tools: Read, Grep     # Restrict tools when skill is active
context: fork                 # Run in isolated subagent
agent: Explore                # Subagent type when context: fork
---

# Skill Title

Your prescriptive, actionable instructions here.
```

## Frontmatter Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Display name (defaults to directory name). Lowercase, hyphens, max 64 chars. |
| `description` | **Yes** | What it does and when to use it. Claude uses this for auto-loading. |
| `user-invocable` | No | `false` = hide from `/` menu. Use for background knowledge. Default: `true` |
| `disable-model-invocation` | No | `true` = only manual `/name` invocation. Use for side-effects. Default: `false` |
| `argument-hint` | No | Hint shown during autocomplete, e.g., `[filename] [format]` |
| `allowed-tools` | No | Comma-separated tools Claude can use without permission |
| `context` | No | `fork` = run in isolated subagent context |
| `agent` | No | Subagent type when `context: fork` (`Explore`, `Plan`, `general-purpose`) |

## Skill Types

| Type | `user-invocable` | `disable-model-invocation` | Use for |
|------|------------------|---------------------------|---------|
| Reference | `false` | (default) | Conventions, patterns, style guides. Claude loads automatically. |
| Task | (default) | `true` | Deployments, commits, side-effects. Manual trigger only. |
| Hybrid | (default) | (default) | Both auto-load and manual invocation work. |

## Writing Effective Skills

### Transform Principles into Patterns

Skills must be **prescriptive and actionable**. Vague principles don't change outputs.

```markdown
# INCORRECT - vague principle
Names should be descriptive and reveal intent.

# CORRECT - actionable pattern
## Function Names
**Pattern**: `<verb>_<noun>` in `snake_case`

| Verb | When to use | Example |
|------|-------------|---------|
| `get_` | Retrieve from memory/cache | `get_user_by_id` |
| `fetch_` | Retrieve from external source | `fetch_api_data` |
| `create_` | Instantiate new object | `create_session` |
```

### Use CORRECT/INCORRECT Examples

Show exactly what to do and what to avoid:

````markdown
```python
# CORRECT - descriptive name with verb_noun pattern
def fetch_user_by_email(email: str) -> User:
    """Fetch user from database by email address."""
    ...

# INCORRECT - generic name, no verb
def get_data(x):
    ...
```
````

### Use Tables for Quick Reference

Tables are scannable and enforceable:

```markdown
| Element | Convention | Example |
|---------|------------|---------|
| Functions | `verb_noun` | `fetch_user`, `validate_input` |
| Variables | `snake_case` | `user_count`, `is_valid` |
| Classes | `PascalCase` | `SearchIndex`, `UserSession` |
```

### Include Validation Commands

When applicable, show how to verify compliance:

```markdown
## Validation Commands

| Check | Command |
|-------|---------|
| Docstring style | `uv tool run pydoclint --style=google <path>` |
| Type checking | `uv run ty check <path>` |
```

## Size Guidelines

- Keep `SKILL.md` under **500 lines**
- Move detailed reference material to separate files in the skill directory
- Reference supporting files from SKILL.md:

```markdown
## Additional Resources

- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

## String Substitutions

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed to skill |
| `$ARGUMENTS[N]` or `$N` | Specific argument by index (0-based) |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `` !`command` `` | Shell command output (runs before skill loads) |

Example:

```yaml
---
name: fix-issue
description: Fix a GitHub issue
argument-hint: [issue-number]
---

Fix GitHub issue $ARGUMENTS following our coding standards.
```

## Skill Directory Structure

```
my-skill/
├── SKILL.md           # Main instructions (required)
├── template.md        # Template for Claude to fill in
├── examples/
│   └── sample.md      # Example output
└── scripts/
    └── validate.sh    # Script Claude can execute
```

## Checklist

Before finalizing a skill, verify:

- [ ] Description clearly states **what** and **when**
- [ ] Instructions are **prescriptive** (patterns, not principles)
- [ ] Includes **CORRECT/INCORRECT** code examples
- [ ] Uses **tables** for quick reference where applicable
- [ ] Under **500 lines** (move details to supporting files)
- [ ] Correct `user-invocable` / `disable-model-invocation` settings
- [ ] Includes **validation commands** if applicable

## Quick Start

1. Create directory: `mkdir -p .claude/skills/$ARGUMENTS`
2. Create `SKILL.md` with frontmatter and instructions
3. Test with `/skill-name` or ask Claude something that triggers auto-load
4. Verify with: "What skills are available?"
