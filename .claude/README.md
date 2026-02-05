# Claude Code Configuration

> **For humans only.** This README explains the `.claude` directory structure for engineers adopting and customizing this setup. Agents should not use this file as context—they read `CLAUDE.md` instead.

## Quick Start

The core workflow is: **plan → implement → review → verify tests → commit**

```bash
/plan <description>           # Create implementation plan
/implement Phase 1 from ...   # Execute a phase
/review                       # Full review (style + substance + test quality)
/review --src-only            # Review source code only
/review --tests-only          # Review tests only
git commit                    # Commit manually
/update-plan                  # Mark phase complete, continue
```

## Why Test Quality Verification Matters

**AI models tend to optimize for the appearance of completion rather than actual quality.** When facing constraints—limited context windows, complex requirements, or approaching output limits—AI often takes shortcuts to avoid appearing to fail. The immediate gratification of "working" code can mask deeper quality issues.

The unified `/review` command includes test quality verification because:

1. **Systematic verification must go beyond "tests pass"**: You need to examine whether tests verify meaningful behavior, not just that they run without errors.

2. **AI defaults to bare-minimum quality**: Unless explicitly pushed, AI will do the minimum to make code function, regardless of maintainability or consistency with existing patterns.

3. **Context exhaustion causes silent degradation**: As the context window fills, test quality often degrades first—you'll see repetitive test data, missing edge cases, and rubber-stamp assertions.

4. **AI can do better when asked**: Models clearly have access to better approaches—they demonstrate this when explicitly asked to review and improve their own work. The default mode is just lower effort.

The `test-reviewer` agent applies the `test-quality` skill to catch these systematic omissions before they become technical debt. Use `/review --tests-only` to focus exclusively on test quality.

**Beyond tests—the bloat problem:**

It takes time to edit working code down to its optimal size and shape. AI often lacks the time and context space to do this during initial implementation. You'll regularly need to ask AI to clean up code, or it starts looking like an overflowing garage where nothing is ever thrown away. The `/clean` command and `code-cleaner` agent exist for this reason.

---

## Usage Guides

Deep dives into specific topics. Start here after you're comfortable with the Quick Start workflow.

| Guide | What You'll Learn |
|-------|-------------------|
| **[Agentic Coding Workflow](usage-guides/agentic-coding-workflow.md)** | Complete walkthrough of the plan → implement → review cycle. Commands, agents, validation, troubleshooting. |
| **[Context Window Management](usage-guides/context-window-management.md)** | Why AI performance degrades as context fills up, and how this configuration uses agents and bundles to keep sessions efficient. |
| **[Reviewer-Friendly PRs](usage-guides/reviewer-friendly-prs.md)** | Creating PRs that respect reviewers' time. Validation checklists, description templates, structuring large changes. |

---

## Architecture Overview

### Design Philosophy

This configuration separates concerns into three distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                        COMMANDS                              │
│           Orchestration: workflows that use agents           │
│       /plan  /implement  /review  /pr-description            │
└─────────────────────────┬───────────────────────────────────┘
                          │ invoke
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         AGENTS                               │
│            Execution: specialists that do work               │
│  planner  code-writer  test-writer  test-reviewer  reviewers │
└─────────────────────────┬───────────────────────────────────┘
                          │ load
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         SKILLS                               │
│          Knowledge: conventions, templates, criteria         │
│   class-design  testing  frameworks  plan-template  ...      │
└─────────────────────────────────────────────────────────────┘
```

**Why this separation matters:**

- **Skills** = Knowledge that multiple agents share (conventions, templates)
- **Agents** = Focused specialists with specific responsibilities
- **Commands** = User-facing workflows that compose agents

### Single Source of Truth

`manifest.json` defines all relationships:

```json
{
  "skills": [{ "name": "class-design", "category": "conventions", ... }],
  "agents": [{ "name": "planner", "depends_on": ["plan-template", ...] }],
  "commands": [{ "name": "plan", "depends_on_agents": ["planner"] }]
}
```

Changes to relationships happen in one place. The manifest drives:
- Bundle generation (what skills each agent receives)
- CLAUDE.md generation (via `/sync-context`)
- Documentation of dependencies

### Bundle Generation

Agents need skill knowledge, but loading skills individually at runtime is inefficient. Instead:

1. **manifest.json** declares which skills each agent depends on
2. **generate_bundles.py** pre-composes skills into bundles
3. **Agents** load a single bundle file with all their context

```bash
# Regenerate bundles after modifying skills
uv run python .claude/scripts/generate_bundles.py
```

Two bundle variants are generated:
- **Full bundle** (`planner.md`): Complete skill content including examples
- **Compact bundle** (`planner-compact.md`): Quick Reference sections only

### Layered Skills

Complex skills split content across files:

```
skills/class-design/
├── SKILL.md      # Main content + Quick Reference table
├── rules.md      # Decision flow and rules
└── examples.md   # Code examples
```

The frontmatter in `SKILL.md` declares layers:

```yaml
---
name: class-design
layers:
  rules: rules.md
  examples: examples.md
---
```

Bundles include all layers. Compact bundles include only Quick Reference.

### Git-Ignored Outputs

Two directories regenerate as needed:

```
.claude/
├── bundles/         # Generated by generate_bundles.py
└── agent-outputs/   # Written by agents at runtime
    ├── plans/
    ├── reviews/
    └── pr-descriptions/
```

Both are `.gitignore`d. Regenerate bundles after skill changes. Agent outputs are timestamped for history.

---

## Directory Structure

```
.claude/
├── CLAUDE.md              # Agent instructions (auto-generated by /sync-context)
├── README.md              # This file (humans only)
├── settings.local.json    # Local settings
│
├── commands/              # User-invocable workflows
│   ├── plan.md
│   ├── implement.md
│   ├── review.md
│   └── ...
│
├── agents/                # Execution specialists
│   ├── planner.md
│   ├── python-code-writer.md
│   └── ...
│
├── skills/                # Knowledge & conventions
│   ├── manifest.json      # Single source of truth
│   ├── class-design/
│   │   ├── SKILL.md
│   │   ├── rules.md
│   │   └── examples.md
│   ├── testing/
│   │   └── SKILL.md
│   └── ...
│
├── bundles/               # Pre-composed context (generated, gitignored)
│   ├── planner.md
│   ├── planner-compact.md
│   └── ...
│
├── agent-outputs/         # Agent work products (generated, gitignored)
│   ├── plans/
│   ├── reviews/
│   └── pr-descriptions/
│
└── scripts/               # Automation
    ├── generate_bundles.py
    └── sync_context.py
```

---

## Customization Guide

### Adding a New Skill

1. **Create the skill directory and files:**
   ```bash
   /create-skill
   # Follow prompts for name, category, description
   ```

2. **Edit the generated SKILL.md** with your conventions

3. **Add to manifest.json** (if not auto-added):
   ```json
   {
     "name": "your-skill",
     "category": "conventions",
     "description": "What this skill provides",
     "user_invocable": false
   }
   ```

4. **Add to agent dependencies** in manifest.json:
   ```json
   {
     "name": "python-code-writer",
     "depends_on": ["your-skill", ...]
   }
   ```

5. **Regenerate bundles:**
   ```bash
   uv run python .claude/scripts/generate_bundles.py
   ```

6. **Update CLAUDE.md:**
   ```bash
   /sync-context
   ```

### Adding a New Agent

1. **Create agent file** in `agents/`:
   ```yaml
   ---
   name: your-agent
   version: 1.0.0
   description: What this agent does
   model: sonnet  # or opus
   bundle: bundles/your-agent.md
   tools:
     - Read
     - Write
     - Edit
   ---

   Instructions for the agent...
   ```

2. **Add to manifest.json:**
   ```json
   {
     "name": "your-agent",
     "description": "What this agent does",
     "model": "sonnet",
     "depends_on": ["skill1", "skill2"]
   }
   ```

3. **Generate bundles and sync:**
   ```bash
   uv run python .claude/scripts/generate_bundles.py
   /sync-context
   ```

### Adding a New Command

1. **Create command file** in `commands/`:
   ```yaml
   ---
   name: your-command
   version: 1.0.0
   description: What this command does
   depends_on_agents:
     - agent-it-uses
   ---

   # Command Title

   Instructions for what this command does...
   ```

2. **Add to manifest.json:**
   ```json
   {
     "name": "your-command",
     "description": "What this command does",
     "depends_on_agents": ["agent-it-uses"]
   }
   ```

3. **Sync context:**
   ```bash
   /sync-context
   ```

### Modifying Conventions

1. **Edit the skill's SKILL.md** (and rules.md/examples.md if layered)
2. **Regenerate bundles** so agents get updated context
3. **Test** by running a command that uses the affected agents

---

## Skill Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **conventions** | How code should be written | `class-design`, `naming-conventions`, `testing` |
| **assessment** | Criteria for code review | `maintainability`, `testability`, `test-quality` |
| **templates** | Output format specifications | `plan-template`, `review-template` |
| **utilities** | Reusable operations | `run-python-safely`, `write-markdown-output` |

---

## Troubleshooting

### Agent doesn't know about a skill
- Check `manifest.json` that the agent's `depends_on` includes the skill
- Regenerate bundles: `uv run python .claude/scripts/generate_bundles.py`

### Command not appearing in /help
- Ensure the command file has correct frontmatter
- Run `/sync-context` to regenerate CLAUDE.md

### Changes to skills not reflected
- Regenerate bundles after any skill modification
- Bundles are gitignored, so they won't auto-update

### CLAUDE.md out of sync
- Run `/sync-context` to regenerate from current disk state
