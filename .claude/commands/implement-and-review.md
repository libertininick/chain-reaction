# Implement Feature With Tests and Review

Implement the following feature: $ARGUMENTS

## Process

1. **Understand the requirement**
   - Analyze the feature request
   - Ask clarifying questions if the scope is unclear
   - Identify affected files and modules

2. **Plan the implementation**
   - Determine which modules need changes
   - Check [frameworks.md](../frameworks.md) for approved frameworks
   - Fetch documentation for any frameworks you'll use

3. **Implement the feature**
   - Follow conventions in [development-conventions.md](../development-conventions.md)
   - Add type hints to all functions
   - Write Google-style docstrings explaining "why"
   - Use fail-fast error handling with clear messages

4. **Validate implementation**
   - Run `uv run ruff check --fix && uv run ruff format` to lint and format code
   - Run `uv run pytest` to verify all tests pass
   - Run `uv run ty check .` to verify all type hints are correct
   - Fix any issues before marking complete

5. **Review**
   - Use the `python-code-reviewer` agent for a final review
   - Address any critical or important issues raised
   - Ignore suggestions related to test coverage on new code; you are not writing tests
