# Generate PR Description

Generate a pull request description from current branch changes: $ARGUMENTS

## What This Does

This command analyzes all changes on the current branch compared to `main` and generates a comprehensive, well-structured PR description.

The generator will:
1. **Analyze branch changes** - Compare current branch to main and understand all modifications
2. **Extract context from plan** (if provided) - Use the implementation plan to understand intent and design decisions
3. **Generate PR description** - Create a formatted description following the required template

## Usage

```
/pr-description
/pr-description --plan <plan-path>
/pr-description --plan <plan-path> --phases <N1,N2,...>
```

**Examples:**
```
/pr-description
/pr-description --plan .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
/pr-description --plan .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md --phases 1,2
```

## Execution Flow

### 1. Gather Branch Information

```bash
# Get current branch name
git branch --show-current

# Get all commits on this branch not in main
git log main..HEAD --oneline

# Get full diff against main
git diff main...HEAD

# Get list of changed files
git diff main...HEAD --name-status
```

### 2. Analyze Changes

For each changed file:
- Categorize by type (source code, tests, documentation, configuration)
- Identify semantic changes (new features, refactors, bug fixes)
- Note any files that touch critical areas

### 3. Extract Plan Context (if provided)

If `--plan` is specified:
- Read the plan document
- Extract the Summary and goals
- Identify design decisions documented in the plan
- Determine which phases were implemented (from `--phases` or by analyzing completed work)
- Identify remaining phases for "Future Phases" section

### 4. Check Development Conventions

Review changes against [development-conventions](../development-conventions/):
- Note any intentional deviations that should be documented
- These MUST be called out in "Key Design Decisions"

### 5. Generate PR Description

Output the PR description in the following format:

```markdown
## Summary

<High-level summary of changes and context for why the changes were made. Should answer: What does this PR do? Why is it needed?>

## What's Included

<Compact list organized by category to help reviewer understand scope at a glance>

**Source Code:**
- `path/to/file.py` - Brief description of change

**Tests:**
- `tests/test_file.py` - What's being tested

**Documentation:**
- `docs/file.md` - What was documented (or note if missing)

**Configuration:**
- `pyproject.toml` - Dependencies added/changed

## Key Design Decisions

<Design decisions to document for reviewer context. Focus on "why this approach" not implementation details>

1. **Decision**: Rationale for why this approach was chosen over alternatives

2. **Convention Deviation** (if any): Any intentional deviations from [development-conventions](../.claude/development-conventions/) with justification

## Critical Areas for Review

<Prioritized areas deserving careful review. Help reviewer focus their attention on what matters most>

1. **`path/to/critical/file.py:L10-L50`** - Description of why this needs careful review (e.g., complex logic, security implications, breaking change)

2. **`path/to/another/file.py`** - Why this is important to review

## Future Phases

<Optional: Only include if this PR is a partial implementation of a larger plan>

The following phases from the [implementation plan](<plan-path>) are planned for future PRs:
- **Phase N**: Brief description of what's coming
- **Phase M**: Brief description of what's coming
```

## Output

The PR description is written to:
```
.claude/agent-outputs/pr-descriptions/pr-<branch-name>-<YYYY-MM-DD>.md
```

The description is also displayed in the terminal for easy copying.

## When to Use This Command

- **Before creating a PR** - Generate description after all changes are committed
- **After completing implementation** - Summarize what was built
- **For documentation** - Create a record of changes and decisions

## Tips

- Run `/review --staged` or `/review --commits main..HEAD` before this command to ensure code quality
- Provide the plan path for richer context in the description
- Review the generated description and adjust as needed before creating the PR

---
