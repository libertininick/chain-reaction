# Claude Code Configuration

> **For humans only.** This README explains the `.claude` directory structure for engineers adopting and customizing this setup. Agents should not use this file as context—they read `CLAUDE.md` instead.

## Quick Start

After pulling `.claude/`:
1. Add `context7` MCP server to Claude:
   - Sign up for the free Contex7 account: https://context7.com/sign-up
   - Generate an API key
   - Connect Claude to the context7 MCP server: https://context7.com/docs/clients/claude-code#local-server

      ```sh
      claude mcp add context7 -- npx -y @upstash/context7-mcp --api-key YOUR_API_KEY
      ```
   - Confirm connection by running `/mcp` inside a Claude session, you should see:
      ```sh
      Manage MCP servers                                                                                                        
      1 server                                                                                                                  
                                                                                                                                 
         Local MCPs (../.claude.json [project: ../repos/buzzai])                     
      ❯ context7 · ✔ connected  
      ```
2. Inside a Claude session run `/sync` command to generate bundles (they're gitignored):

   ```sh
   /sync
   # Or manually from your terminal: uv run python .claude/scripts/sync_context.py
   ```

   Note, each time you pull changes from .claude, add a skill, command, or agent, or update a setting you should run `/sync` to ensure the context bundles are up to date.

## Core Workflow
The core workflow is: **plan → implement → review → verify tests → commit**

Custom Claude commands for project:

```bash
/plan <description>           # Create implementation plan
/implement Phase 1 from ...   # Execute a phase
/review                       # Full review (style + substance + test quality)
/review --src-only            # Review source code only
/review --tests-only          # Review tests only
git commit                    # Commit manually
/update-plan                  # Mark phase complete, continue
```

Every command supports `--help` to show usage and examples (e.g., `/review --help`).

## Usage Guides

Deep dives into specific topics. Start here after you're comfortable with the Quick Start workflow.

| Guide | What You'll Learn |
|-------|-------------------|
| **[Understanding LLM Coding Agents](usage-guides/understanding-llm-coding-agents.md)** | Step-by-step guide to how AI coding agents actually work. Pattern matching, tool use, context windows, and agentic loops demystified. |
| **[Agentic Coding Workflow](usage-guides/agentic-coding-workflow.md)** | Complete walkthrough of the plan → implement → review cycle. Commands, agents, validation, troubleshooting. |
| **[Context Window Management](usage-guides/context-window-management.md)** | Why AI performance degrades as context fills up, and how this configuration uses agents and bundles to keep sessions efficient. |
| **[Reviewer-Friendly PRs](usage-guides/reviewer-friendly-prs.md)** | Creating PRs that respect reviewers' time. Validation checklists, description templates, structuring large changes. |
| **[Thinking Tokens & Model Selection](usage-guides/thinking-llms-guide.md)** | How thinking tokens actually work, when extended thinking helps (and when it doesn't), and practical model selection guidance for code generation. |

---

## Architecture Overview

### Design Philosophy

This configuration separates concerns into three distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                        COMMANDS                             │
│           Orchestration: workflows that use agents          │
│       /plan  /implement  /review  /pr-description           │
└─────────────────────────┬───────────────────────────────────┘
                          │ invoke
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         AGENTS                              │
│            Execution: specialists that do work              │
│ planner  code-writer  test-writer  test-reviewer  reviewers │
└─────────────────────────┬───────────────────────────────────┘
                          │ load
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         SKILLS                              │
│          Knowledge: conventions, templates, criteria        │
│  class-design  test-writing  frameworks  plan-template  ... │
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
  "agents": [{ "name": "planner", "depends_on_skills": ["plan-template", ...] }],
  "commands": [{ "name": "plan", "depends_on_agents": ["planner"] }]
}
```

Changes to relationships happen in one place. The manifest drives:
- Bundle generation (what skills each agent receives)
- CLAUDE.md generation (via `/sync`)
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
├── CLAUDE.md              # Agent instructions (auto-generated by /sync)
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
├── manifest.json          # Single source of truth
│
├── skills/                # Knowledge & conventions
│   ├── class-design/
│   │   ├── SKILL.md
│   │   ├── rules.md
│   │   └── examples.md
│   ├── test-writing/
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
     "depends_on_skills": ["your-skill", ...]
   }
   ```

5. **Regenerate bundles:**
   ```bash
   uv run python .claude/scripts/generate_bundles.py
   ```

6. **Update CLAUDE.md:**
   ```bash
   /sync
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
     "depends_on_skills": ["skill1", "skill2"]
   }
   ```

3. **Generate bundles and sync:**
   ```bash
   uv run python .claude/scripts/generate_bundles.py
   /sync
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
   /sync
   ```

### Modifying Conventions

1. **Edit the skill's SKILL.md** (and rules.md/examples.md if layered)
2. **Regenerate bundles** so agents get updated context
3. **Test** by running a command that uses the affected agents

---

## Skill Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **conventions** | How code should be written | `class-design`, `naming-conventions`, `test-writing` |
| **assessment** | Criteria for code review | `maintainability`, `testability`, `test-quality` |
| **templates** | Output format specifications | `plan-template`, `review-template` |
| **utilities** | Reusable operations | `run-python-safely`, `write-markdown-output` |

---

## Troubleshooting

### Agent doesn't know about a skill
- Check `manifest.json` that the agent's `depends_on_skills` includes the skill
- Regenerate bundles: `uv run python .claude/scripts/generate_bundles.py`

### Command not appearing in /help
- Ensure the command file has correct frontmatter
- Run `/sync` to regenerate CLAUDE.md

### Changes to skills not reflected
- Regenerate bundles after any skill modification
- Bundles are gitignored, so they won't auto-update

### CLAUDE.md out of sync
- Run `/sync` to regenerate from current disk state
