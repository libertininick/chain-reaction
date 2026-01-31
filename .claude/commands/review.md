# Code Review

Conduct a code review: $ARGUMENTS

## Review Process

This command orchestrates a two-phase review using specialized agents, then aggregates results into a unified report.

### Phase 1: Style Review

Launch the `code-style-reviewer` agent with:
- The code diff or files to review
- Implementation plan context (if `--plan` provided)

Wait for completion before proceeding.

### Phase 2: Substance Review

After style review completes, launch the `code-substance-reviewer` agent with:
- The same code diff or files
- Implementation plan context (if `--plan` provided)

Wait for completion.

### Phase 3: Aggregate and Write Report

After both reviews complete:

1. **Collect findings** from both reviewers
2. **Identify overlapping concerns** - issues flagged by both reviewers indicate higher priority
3. **Determine verdict**:
   - APPROVE: No critical issues from either reviewer
   - NEEDS CHANGES: Critical issues found OR many significant improvements needed
   - REJECT: Fundamental design problems requiring rearchitecture
4. **Invoke `review-template` skill** for output format
5. **Write unified report** to `.claude/agent-outputs/reviews/<YYYY-MM-DDTHHmmssZ>-<scope>-review.md`

**IMPORTANT**: Run reviewers sequentially, NOT in parallel.

## Specialized Reviewers

| Reviewer | Model | Focus |
|----------|-------|-------|
| **code-style-reviewer** | Sonnet | Conventions, naming, docstrings, type hints, imports, organization, Pythonic patterns |
| **code-substance-reviewer** | Opus | Correctness, edge cases, error handling, design quality, maintainability, testability |

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

When provided, the reviewers will:
- Understand the **intended design** from the plan
- Verify the implementation **matches the plan's requirements**
- Check that **acceptance criteria** are addressed

**Examples:**
```
/review --staged --plan .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md --phase 2
/review src/foo.py --plan .claude/agent-outputs/plans/2024-01-22T143052Z-new-feature-plan.md
```

## What Gets Reviewed

### Style Review (code-style-reviewer)

Rule-based checks using convention skills:

| Skill | What's Checked |
|-------|----------------|
| `naming-conventions` | Variables, functions, classes, modules |
| `docstring-conventions` | Presence, format, completeness |
| `type-hints` | Coverage and correctness |
| `code-organization` | Imports, module structure, file layout |
| `pythonic-conventions` | Comprehensions, built-ins, context managers |
| `function-design` | Signatures, parameters, return types |
| `class-design` | Interfaces, attributes, method organization |

### Substance Review (code-substance-reviewer)

Design and correctness analysis using:

| Skill | What's Checked |
|-------|----------------|
| `class-design` | Coupling, cohesion, composition, inheritance |
| `function-design` | Responsibility, complexity, parameters |
| `maintainability` | Readability, change tolerance, hidden assumptions |
| `testability` | Dependency injection, global state, pure functions |

Plus correctness analysis: requirements match, logic correctness, edge cases, error handling

## Output

Review documents are saved to:
```
.claude/agent-outputs/reviews/<YYYY-MM-DDTHHmmssZ>-<scope>-review.md
```

Where:
- Timestamp is UTC in ISO format (e.g., `2024-01-22T143052Z`)
- `<scope>` is derived from:
  - File name (single file): `2024-01-22T143052Z-parser-review.md`
  - Directory/module (multiple files): `2024-01-22T143052Z-tools-review.md`
  - Plan phase: `2024-01-22T143052Z-phase-2-api-refactor-review.md`
  - Commit: `2024-01-22T143052Z-commit-abc123f-review.md`
  - Staged changes: `2024-01-22T143052Z-staged-review.md`

### Report Structure

The merged report contains:

1. **Summary** - Scope, verdict, key finding
2. **Critical Issues** - Must fix before merge (from either reviewer)
3. **Improvements** - Should address, grouped by category
4. **Nitpicks** - Minor items, one line each
5. **Overlapping Concerns** - Issues flagged by both reviewers (elevated priority)

Empty sections are omitted. Use `review-template` skill for exact format.

## Scope Determination

Derive `<scope>` for output filename from:

| Review Target | Scope |
|---------------|-------|
| Single file `foo.py` | `foo` |
| Multiple files in `tools/` | `tools` |
| Commit `abc123f` | `commit-abc123f` |
| Staged changes | `staged` |
| Plan phase 2 | `phase-2-<plan-name>` |

## When to Use This Command

- **After implementing a feature** - Verify quality before committing
- **After refactoring** - Ensure changes maintain code quality
- **Before a PR** - Get comprehensive feedback on all changes
- **After `/implement`** - Review the implemented phase

## Important Notes

- The reviewers **do NOT modify any code** - they only generate review documents
- Reviews run sequentially (style first, then substance) to ensure stability
- Overlapping findings from both reviewers indicate higher priority issues
- For test writing based on review findings, use `python-test-writer` agent
- For implementing review suggestions, use `python-code-writer` agent

---
