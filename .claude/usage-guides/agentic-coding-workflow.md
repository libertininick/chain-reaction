# Agentic Coding Workflow Guide

A structured approach for working with Claude Code in this repository using specialized agents, commands, and conventions.

---

## Overview: The Plan → Implement → Review Cycle

This repository is configured with specialized agents and commands that automate the agentic coding workflow:

```
/plan <description>
       │
       ▼
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   /implement Phase N                  /review                 │
│        │                                 │                    │
│        ▼                                 ▼                    │
│   ┌──────────┐    ┌──────────┐    ┌─────────────────────────┐ │
│   │Code Write│───▶│Test Write│───▶│ Style + Substance +     │ │
│   │  Agent   │    │  Agent   │    │ Test Quality Reviewers  │ │
│   └──────────┘    └──────────┘    └─────────────────────────┘ │
│        │                                      │               │
│        ▼                                      ▼               │
│   Validation                           Unified Review         │
│   (ruff, ty, pytest)                   Findings               │
│                                               │               │
│        ▲              ┌──────────────────────────┐            │
│        │              │  git commit (manual)     │◀───────────┘
│        │              │  /update-plan <path>     │
│        └──────────────│  Next phase...           │
│                       └──────────────────────────┘
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Key components:**
- **7 specialized agents** with appropriate models and context bundles
- **8 commands** that orchestrate agent workflows
- **20 skills** that define coding conventions and standards
- **Automatic outputs** saved to `.claude/agent-outputs/`

---

## Phase 1: Frame Your Objective

Before running `/plan`, establish a clear picture of what you're building.

**What to include:**

- The specific outcome you want to achieve
- Why this matters (context helps agents make better decisions)
- What success looks like in concrete terms
- Constraints (approved frameworks, existing patterns, performance requirements)

**Example of a weak objective:**
> "Add data validation."

**Example of a strong objective:**
> "Add Pydantic validation to the DataFrame toolkit. Each tool should validate its inputs using Pydantic models, with clear error messages for invalid arguments. Success means: all tool inputs are validated, existing tests pass, new validation tests cover edge cases, and the code follows patterns in `src/my-library/module/tools/`."

**Tips:**

- Reference existing code paths the agent should follow
- Check the `frameworks` skill for approved libraries before requesting new dependencies
- Mention what's explicitly out of scope to prevent over-engineering

---

## Phase 2: Create a Plan with `/plan`

The `/plan` command dispatches to the **planner agent**  which creates a detailed implementation plan.

**Command syntax:**
```
/plan <description>
```

**Example:**
```
/plan Add Pydantic validation models to DataFrame toolkit tools with comprehensive error handling
```

**What the planner agent does:**

1. Loads its context bundle (plan-template + development conventions)
2. Explores the codebase to understand existing patterns
3. Creates a phased plan with clear deliverables
4. Saves output to `.claude/agent-outputs/plans/<timestamp>-<scope>-plan.md`

**Plan structure (from plan-template skill):**

```markdown
# Implementation Plan: [Title]

## Objective
[What we're building and why]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Phases

### Phase 1: [Name]
**Goal:** [Single-sentence summary]

#### Implementation Steps
1. Step with specific file paths
2. Step with expected patterns

#### Test Steps
1. Test case description
2. Edge case coverage

#### Validation
- [ ] `uv run ruff format && uv run ruff check`
- [ ] `uv run ty check`
- [ ] `uv run pytest tests/path/`

#### Done When
- Specific completion criteria
```

**Your responsibilities:**

- Review the plan before proceeding
- Push back if phases are too large (ask to subdivide)
- Validate the plan against your objective
- Save or note the plan path for subsequent commands

---

## Phase 3: Implement with `/implement`

The `/implement` command orchestrates multiple agents to build a single phase.

**Command syntax:**
```
/implement Phase N from <plan-path>
```

**Example:**
```
/implement Phase 1 from .claude/agent-outputs/plans/2026-02-04T120000Z-pydantic-validation-plan.md
```

**What happens:**

1. **Parse phase requirements** from the plan
2. **Code-writer agent**:
   - Loads bundle (frameworks + coding conventions)
   - Implements source code following existing patterns
   - Runs validation: `ruff format`, `ruff check`, `ty check`
3. **Test-writer agent**:
   - Loads bundle (testing conventions)
   - Writes pytest tests for the new code
   - Covers success paths, edge cases, error handling
4. **Code-cleaner agent**:
   - Cleans and organizes new/modified files
   - Removes bloat, simplifies structure
5. **Final validation**: All lint/type/test commands pass

**Validation commands run automatically:**
```bash
uv run ruff format          # Format code
uv run ruff check           # Lint (includes complexity checks)
uv run ty check             # Type check
uv run pytest tests/        # Run tests
```

**Your responsibilities:**

- Read the generated code—you own it now
- Run tests manually if you want additional verification
- Check for scope creep (did the agent add things not in this phase?)
- Stage and commit when satisfied

---

## Phase 4: Review with `/review`

The `/review` command runs both style and substance reviews sequentially.

**Command syntax:**
```
/review [target] [--plan <path>] [--src-only | --tests-only]
```

**Target options:**
- `--staged` — Review staged changes (most common)
- `--commits main..HEAD` — Review all commits on branch
- `path/to/file.py` — Review specific files
- (no target) — Defaults to `--staged`

**Filtering options:**
- `--src-only` — Review only source files (style + substance reviewers)
- `--tests-only` — Review only test files (all three reviewers)
- (no filter) — Reviews all files with appropriate reviewers

**Example:**
```
/review --staged --plan .claude/agent-outputs/plans/2026-02-04T120000Z-pydantic-validation-plan.md
```

**What happens:**

1. **Classify files** as source or test files (auto-detected)

2. **Run tests** (if test files in scope) to verify they pass

3. **Style reviewer** checks all files for:
   - Naming conventions
   - Docstring completeness
   - Type hint coverage
   - Import organization
   - Code organization patterns

4. **Substance reviewer** checks all files for:
   - Correctness and edge cases
   - Error handling completeness
   - Design quality
   - Maintainability
   - Testability

5. **Test reviewer** checks test files for:
   - Substantive assertions (not rubber stamps)
   - True functionality testing (behavior, not implementation)
   - Edge case coverage
   - Test data variety
   - Fixture and mock discipline

6. **Aggregate findings** into severity categories:
   - **Critical** — Must fix before merging
   - **Improvement** — Should fix, meaningful quality impact
   - **Nitpick** — Nice to have, stylistic preference
   - **Overlapping concerns** — Issues found by multiple reviewers (high priority)

7. **Save output** to `.claude/agent-outputs/reviews/<timestamp>-<scope>-review.md`

8. **Verdict**: APPROVE, NEEDS CHANGES, or REJECT

**Your responsibilities:**

- Address critical issues before committing
- Consider improvement suggestions
- Nitpicks are optional but indicate polish opportunities

---

## Phase 5: Commit Changes (Manual)

Claude Code never commits unless explicitly instructed. After successful implementation and review:

```bash
git add -p                    # Stage changes selectively
git commit -m "feat(scope): implement [phase description]

- Key change 1
- Key change 2

Plan: .claude/agent-outputs/plans/<plan-file>.md"
```

**Tips:**

- Use conventional commit format (feat, fix, refactor, test, docs)
- Reference the plan file for traceability
- Commit working code before moving on—never leave the repo broken

---

## Phase 6: Update Plan with `/update-plan`

After completing a phase, sync the plan with current state.

**Command syntax:**
```
/update-plan <plan-path>
```

**Example:**
```
/update-plan .claude/agent-outputs/plans/2026-02-04T120000Z-pydantic-validation-plan.md
```

**What happens:**

1. Fetches and merges latest main (resolves conflicts if any)
2. Analyzes what changed in main that affects the plan
3. Reviews completed phases against actual implementation
4. Updates remaining phases based on lessons learned
5. Marks completed phases as done

**Why this matters:**

- Code changes things—next phases may need adjustment
- You may have discovered edge cases or new requirements
- Main branch may have evolved while you worked
- Fresh planning prevents drift from the original vision

---

## Phase 7: Iterate Until Complete

Repeat the cycle for each remaining phase:

1. `/implement Phase N+1 from <plan-path>`
2. `/review --staged --plan <plan-path>`
3. `git commit -m "..."`
4. `/update-plan <plan-path>`

**Checkpoint questions after each iteration:**

- Does the code still align with the original objective?
- Are we accumulating technical debt that needs addressing?
- Is the remaining plan still realistic?
- Should we adjust scope based on what we've learned?

**Warning signs to pause and reassess:**

- Implementation diverging significantly from plan
- Tests becoming brittle or hard to write
- Growing list of "fix later" items
- Unclear how current work connects to the objective

---

## Phase 8: Final Review and PR

Once all phases are complete:

**1. Run comprehensive code review:**
```
/review --commits main..HEAD --plan <plan-path>
```

This includes style, substance, and test quality review for all files.

**2. Address any final issues**

**3. Generate PR description:**
```
/pr-description --plan <plan-path> --phases 1,2,3
```

This creates a structured PR description at `.claude/agent-outputs/pr-descriptions/`.

**4. Open the PR**

---

## Quick Reference: Commands

| Command | Purpose | Output Location |
|---------|---------|-----------------|
| `/plan <desc>` | Create implementation plan | `agent-outputs/plans/` |
| `/implement Phase N from <path>` | Execute a plan phase | Modified source files |
| `/review [target]` | Full review (style + substance + test quality) | `agent-outputs/reviews/` |
| `/review --src-only` | Source code review only | `agent-outputs/reviews/` |
| `/review --tests-only` | Test quality review only | `agent-outputs/reviews/` |
| `/update-plan <path>` | Sync plan with reality | Updated plan file |
| `/pr-description` | Generate PR description | `agent-outputs/pr-descriptions/` |
| `/create-skill` | Scaffold new skill | `skills/<name>/` |
| `/sync-context` | Regenerate CLAUDE.md and bundles | Various config files |

---

## Agents and Their Roles

| Agent | Model | When Used | What It Knows |
|-------|-------|-----------|---------------|
| **planner** | Opus | `/plan` | Plan template, all development conventions |
| **python-code-writer** | Opus | `/implement` | Frameworks, all code conventions |
| **python-test-writer** | Opus | `/implement` | Testing conventions, pytest patterns |
| **code-style-reviewer** | Sonnet | `/review` | Style conventions, naming, organization |
| **code-substance-reviewer** | Opus | `/review` | Design, correctness, maintainability |
| **test-reviewer** | Sonnet | `/review` | Test quality, coverage completeness, assertions |
| **code-cleaner** | Opus | `/implement`, `/clean` | Code organization, simplification |

Each agent loads a **context bundle**—pre-composed skill content that gives it exactly the knowledge it needs.

---

## Validation Commands

These run automatically during `/implement` and should pass before committing:

```bash
uv run ruff format                    # Format code
uv run ruff check                     # Lint (includes C901 complexity)
uv run ty check                       # Type check
uv run pydoclint \                    # Docstring validation
    --style=google \
    --allow-init-docstring=True       
uv run pytest                         # Run tests
uv run pytest --cov                   # With coverage
```

---

## Principles to Remember

1. **Commands orchestrate, agents execute:** Use the commands—they handle agent coordination and context loading.

2. **Plans are living documents:** Update them as reality unfolds with `/update-plan`.

3. **Two-stage review catches more:** Style review (fast, conventions) + substance review (thorough, design).

4. **Verify test quality explicitly:** AI tends to optimize for appearance over substance. Passing tests don't guarantee meaningful tests. The `/review` command includes test quality checks automatically; use `--tests-only` to focus exclusively on test quality.

5. **You own the code:** Review everything. Agents are capable but not infallible. AI can do better when pushed—its default is often minimal effort.

6. **Commit manually:** Claude Code never commits unless you explicitly ask—this keeps you in control.

7. **Trust the conventions:** Skills encode project standards. Agents load them automatically via bundles.

8. **Outputs are saved:** Plans, reviews, and PR descriptions persist in `agent-outputs/` for reference.

---

## Troubleshooting

**Agent seems to lack context about conventions:**
- Run `/sync-context` to regenerate bundles
- Check that `manifest.json` lists correct skill dependencies

**Plan doesn't match what I want:**
- Review the plan before `/implement`
- Ask for revisions or create a new plan with clearer objective

**Implementation diverges from plan:**
- Stop and run `/update-plan` to realign
- Break large phases into smaller ones

**Review finds many issues:**
- `/implement` should auto-fix critical issues
- For persistent problems, the plan may need revision

**Need a new skill or convention:**
- Use `/create-skill` to scaffold
- Add to `manifest.json` dependencies
- Run `/sync-context` to regenerate bundles

**Tests look suspicious or too simple:**
- Run `/review --tests-only` to audit test quality
- Look for rubber-stamp assertions (`assert result is not None`)
- Check for repetitive test data (same values in every test)
- Verify edge cases are actually tested

**Test quality degrades later in implementation:**
- This is common as context fills—AI starts taking shortcuts
- Run `/review --tests-only` on all new test files before committing
- Consider breaking large phases into smaller chunks
- Ask explicitly for varied test data and edge case coverage
