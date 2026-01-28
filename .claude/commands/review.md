# Code Review

Review code using the python-code-reviewer agent: $ARGUMENTS

## What This Does

This command invokes the **python-code-reviewer agent** to conduct a thorough code review and generate actionable recommendations.

The reviewer will:
1. **Analyze the specified code** - Read and understand the implementation
2. **Check against conventions** - Verify compliance with [development-conventions](../development-conventions/)
3. **Generate review document** - Write findings to `.claude/reviews/review-<scope>-<YYYY-MM-DD>.md`

## Usage

### Review Specific Files
```
/review <file1> [file2] [file3]...
```

**Examples:**
```
/review src/chain_reaction/tools/parser.py
/review src/chain_reaction/tools/parser.py tests/tools/test_parser.py
```

### Review a Commit
```
/review --commit <hash>
```

Reviews all files changed in the specified commit.

**Examples:**
```
/review --commit abc123f
/review --commit HEAD
```

### Review a Commit Range
```
/review --commits <base>..<head>
```

Reviews all files changed between two commits.

**Examples:**
```
/review --commits main..HEAD
/review --commits abc123f..def456a
```

### Review Staged Changes
```
/review --staged
```

Reviews all currently staged files (useful before committing).

### Review Unstaged Changes
```
/review --unstaged
```

Reviews all files with unstaged modifications.

## Adding Plan Context (Optional)

Add implementation context from a plan document:

```
/review <target> --plan <plan-path> [--phase <N>]
```

When provided, the reviewer will:
- Understand the **intended design** from the plan
- Verify the implementation **matches the plan's requirements**
- Check that **acceptance criteria** are addressed

**Examples:**
```
/review --staged --plan .claude/plans/plan-api-refactor-2024-01-22.md --phase 2
/review src/foo.py --plan .claude/plans/plan-new-feature.md
```

## What Gets Reviewed

The reviewer checks against ALL sections of [development-conventions](../development-conventions/):

| Category | What's Checked |
|----------|----------------|
| **Architecture** | Module design, separation of concerns, coupling |
| **Code Quality** | Readability, naming, docstrings, simplicity |
| **Python Best Practices** | Type hints, Pythonic patterns, PEP 8 |
| **Design Principles** | Composition over inheritance, DRY, single responsibility |
| **Testing** | Testability, edge case handling, coverage gaps |
| **Framework Compliance** | Only approved frameworks per [frameworks.md](../frameworks.md) |

## Output

Review documents are saved to:
```
.claude/reviews/review-<scope>-<YYYY-MM-DD>.md
```

Where `<scope>` is derived from:
- File name (single file): `review-parser-2024-01-22.md`
- Directory/module (multiple files): `review-tools-2024-01-22.md`
- Plan phase: `review-phase-2-api-refactor-2024-01-22.md`
- Commit: `review-commit-abc123f-2024-01-22.md`

## When to Use This Command

- **After implementing a feature** - Verify quality before committing
- **After refactoring** - Ensure changes maintain code quality
- **Before a PR** - Get comprehensive feedback on all changes
- **After `/implement`** - Review the implemented phase

## Important Notes

- The reviewer **does NOT modify any code** - it only generates review documents
- For test writing based on review findings, use `python-test-writer` agent
- For implementing review suggestions, use `python-code-writer` agent

---

