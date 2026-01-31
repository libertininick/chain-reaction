# Implement Plan

Implement one or more phases of plan: $ARGUMENTS

## What This Does

This command orchestrates implementation of phases from an approved plan document by dispatching work to specialized agents.

## Usage

```
/implement Phase <N> from <plan-path>           # Single phase
/implement Phase <N1>, <N2>, and <N3> from <plan-path>  # Multiple phases
/implement <plan-path>                          # Entire plan
```

**Examples:**
```
/implement Phase 1 from .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
/implement Phase 3 and 4 from .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
/implement .claude/agent-outputs/plans/2024-01-22T143052Z-api-refactor-plan.md
```

## Prerequisites

1. Create a plan first using `/plan <feature-description>`
2. Have the plan approved and saved to `.claude/agent-outputs/plans/<YYYY-MM-DDTHHmmssZ>-<scope>-plan.md`

## Execution Flow

For each specified phase:

1. **Parse the Plan**
   - Read the plan document
   - Extract requirements for the specified phase(s)
   - Identify files to create/modify

2. **Implement Source Code**
   - Dispatch to `python-code-writer` agent
   - Agent applies relevant development convention skills (`frameworks`, `naming-conventions`, etc.)
   - Agent checks that docstrings, type hints, and coding conventions are properly followed

3. **Implement Tests**
   - Dispatch to `python-test-writer` agent
   - Agent applies `testing` skill for test conventions
   - Agent checks that docstrings, type hints, and testing conventions are properly followed

4. **Validate**
   - Run validation commands per [CLAUDE.md](../CLAUDE.md)

## After Implementation

- **Code Review**: Use `python-code-reviewer` agent
- **Next Phase**: Run `/implement Phase <N+1> from <same-plan>`
- **Integration**: Verify the implementation integrates with existing code
