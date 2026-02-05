---
name: review-tests
version: 1.0.0
description: Review test quality using the test-reviewer agent
depends_on_agents:
  - test-reviewer
depends_on_skills:
  - review-template
  - write-markdown-output
---

# Review Tests

Review test quality: $ARGUMENTS

## Review Process

This command dispatches test files to the `test-reviewer` agent for quality assessment.

### Phase 1: Resolve Target Files

Determine which test files to review based on arguments.

### Phase 2: Run Tests

Execute `uv run pytest <test-files> -v` to verify tests pass before reviewing.

### Phase 3: Test Quality Review

Launch the `test-reviewer` agent with:
- The test files to review
- Results from test execution

Wait for completion.

### Phase 4: Write Report

After review completes:

1. **Collect findings** from the reviewer
2. **Determine verdict**:
   - APPROVE: No critical issues, tests are substantive and well-organized
   - NEEDS CHANGES: Critical issues found (rubber stamps, missing coverage, tests don't run)
   - REJECT: Fundamental problems requiring rewrite (most tests are meaningless)
3. **Invoke `review-template` skill** for output format
4. **Use `write-markdown-output` skill** to write the report:

```bash
uv run python .claude/skills/write-markdown-output/scripts/write_markdown_output.py \
    -s "<scope>-test-review" \
    -c "<review-content>" \
    -o ".claude/agent-outputs/reviews"
```

## Usage

### Review Specific Test Files
```
/review-tests <test-file1> [test-file2]...
```

**Examples:**
```
/review-tests tests/tools/test_parser.py
/review-tests tests/retrieval/test_search.py tests/retrieval/test_embeddings.py
```

### Review Tests by Glob Pattern
```
/review-tests <glob-pattern>
```

**Examples:**
```
/review-tests tests/tools/*.py
/review-tests tests/**/*test_*.py
```

### Review Staged Test Files
```
/review-tests --staged
```

Reviews all staged test files (files matching `test_*.py` or `*_test.py`).

### Review Tests with Execution
```
/review-tests <target> --with-run
```

Explicitly runs tests and includes pass/fail results in the review. (Tests are run by default, but this flag ensures verbose output is captured.)

## What Gets Reviewed

The `test-reviewer` agent evaluates tests against the `test-quality` skill:

| Category | What's Checked |
|----------|----------------|
| Substantive assertions | Tests prove something meaningful, not rubber stamps |
| True functionality | Tests verify behavior, not implementation details |
| Test organization | Tests mirror source structure, cohesive groupings |
| Edge case coverage | Error paths and boundary conditions tested |
| Test data variety | Realistic, varied data; parametrization used appropriately |
| Fixture usage | Fixtures reduce duplication without tight coupling |
| Mock discipline | Mocks used only when necessary |
| Tests run | Tests pass without errors or warnings |

## Output

Review documents are written using the `write-markdown-output` skill to:
```
.claude/agent-outputs/reviews/<timestamp>-<scope>-test-review.md
```

Where `<scope>` is derived from:
- Single file `test_parser.py`: `test-parser-test-review.md`
- Directory `tests/tools/`: `tools-test-review.md`
- Staged files: `staged-test-review.md`

### Report Structure

The report contains:

1. **Summary** - Scope, verdict, key finding
2. **Critical Issues** - Must fix (rubber stamps, tests don't run, missing assertions)
3. **Improvements** - Should address (missing edge cases, excessive mocking)
4. **Nitpicks** - Minor items (naming, missing docstrings)

Empty sections are omitted. Use `review-template` skill for exact format.

## When to Use This Command

- **After writing new tests** - Verify tests are substantive before committing
- **After `/implement`** - Review the generated tests
- **Before a PR** - Ensure test quality meets standards
- **When tests seem suspicious** - Audit tests that might be rubber stamps

## Important Notes

- The reviewer **does NOT modify any tests** - only generates review documents
- Tests are run before review to verify they pass
- For fixing issues found in review, use `python-test-writer` agent
- This command focuses on **test quality**, not **code correctness** (use `/review` for that)
