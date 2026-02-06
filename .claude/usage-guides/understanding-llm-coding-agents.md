# Understanding LLM Coding Agents

A step-by-step guide to demystifying how AI coding agents actually work.

---

## Step 1: The LLM Generates Code by Pattern Matching

An LLM has been trained on billions of lines of code. Every design pattern, every framework idiom, every common algorithm — it has seen countless examples. When you give it a prompt, it activates the neural pathways most associated with that input and produces the statistically most likely output.

That's it. There is no "understanding." There is no memory. There is no reasoning engine hiding inside. The model receives input tokens, activates neurons, and generates output tokens — one at a time, each one being the most probable next token given everything before it.

This makes LLMs remarkably good at generating code that *looks right*, because they have absorbed the patterns of what right looks like across an enormous corpus.

But there are caveats:

- **The knowledge is stale.** Training has a cutoff date. The model doesn't know about the library version you released last month or the API that changed last week.
- **Modern usage is underrepresented.** The training data skews toward whatever was publicly available at scale — which means newer patterns, frameworks, and idioms are less well-represented than established ones.
- **Most code is mediocre.** The model trained on *all* code, not just the best code. Stack Overflow answers, tutorial snippets, abandoned repos, copy-pasted boilerplate — it's all in there. The model's "default" output reflects the average, not the exceptional.

## Step 2: We Shape the Output by Controlling the Input

Here's the key insight: since the model generates output based entirely on its input, **we can influence the output by controlling what goes into the input.**

This is why prompting matters. If you paste your team's coding conventions, a few examples of well-written functions in your style, and a clear description of what you want — the model will mimic *those* patterns instead of defaulting to the average of its training data.

```
┌─────────────────────────────────┐
│         Context Window          │
│                                 │
│  System prompt                  │
│  + Your coding standards        │
│  + Examples of preferred style  │
│  + Description of the task      │
│                                 │
│  ──────────────────────────►    │
│         Model generates         │
│     code that mirrors YOUR      │
│     patterns, not generic ones  │
└─────────────────────────────────┘
```

This is the entire mechanism behind "skills," "custom instructions," and "system prompts" — they are just text prepended to the input so the model's pattern matching locks onto your preferred patterns rather than the internet's average.

## Step 3: The Agent Wrapper Creates the Illusion of Memory

The LLM itself has no memory. Each time it generates a response, it starts completely fresh. It does not remember what you asked five minutes ago. It does not know it just wrote a function for you.

The **agent wrapper** solves this by replaying the entire conversation history as input every single turn.

```
Turn 1:  [system prompt] + [user message]                    → LLM → response
Turn 2:  [system prompt] + [user msg + response + user msg]  → LLM → response
Turn 3:  [system prompt] + [entire conversation so far]      → LLM → response
```

From the model's perspective, every turn is the first turn. It just happens to receive a very detailed input that includes everything that "happened" before. The continuity you experience — the sense that the model "remembers" your project, your preferences, the bug you're chasing — is constructed entirely by the wrapper feeding the full history back in.

This also explains why long conversations degrade. The context window has a finite size. As the conversation grows, older content gets truncated or compressed, and the model loses access to earlier context. It's not "forgetting" — it literally can't see it anymore.

## Step 4: Tool Calling Gives the System Agency

Up to this point, the model can only generate text. It can *suggest* running a test or *describe* a file change, but it can't actually do anything. Tool calling changes this.

Tools are described in the system prompt alongside everything else. Each tool has a name, a description, and a schema for its parameters. The model has been trained to recognize when a tool would help and to emit a structured tool call instead of plain text.

```
┌──────────────────────────────────────────┐
│              Context Window              │
│                                          │
│  System prompt                           │
│  + Tool: run_terminal_command            │
│      "Execute a shell command"           │
│  + Tool: read_file                       │
│      "Read contents of a file"           │
│  + Tool: write_file                      │
│      "Write content to a file"           │
│                                          │
│  User: "Run the tests for my project"   │
│                                          │
│  ──────────────────────────►             │
│  Model output:                           │
│    call run_terminal_command             │
│    args: {"command": "uv run pytest"}    │
└──────────────────────────────────────────┘
```

The model isn't "deciding" in any deep sense. It's doing the same thing it always does — generating the most likely next tokens given the input. But because the input includes tool descriptions and the model has been trained to emit tool calls when appropriate, the output happens to be a structured action instead of prose.

A tool can be as simple as a hardcoded router: *if the user mentions running tests, execute `uv run pytest`*. Or it can be a full-featured function that reads files, queries databases, or makes API calls. The model doesn't care — it just emits the call. The agent wrapper handles execution.

## Step 5: The Feedback Loop Is Where the Power Lives

Everything up to this point is useful but limited. The model generates code, we shape it with context, the wrapper maintains history, and tools let it take actions. But the real power of a coding agent comes from **closing the loop**: feeding the results of tool calls back into the model as new input.

```
┌─────────────────────────────────────────────────────────┐
│                    The Agent Loop                       │
│                                                         │
│  1. Model sees: conversation + task                     │
│     → generates: tool call (write code to file)         │
│                                                         │
│  2. Wrapper executes tool, captures output              │
│     → feeds result back into context                    │
│                                                         │
│  3. Model sees: conversation + task + code + result     │
│     → generates: tool call (run tests)                  │
│                                                         │
│  4. Wrapper executes tests, captures output             │
│     → feeds result back into context                    │
│                                                         │
│  5. Model sees: conversation + task + code + test fail  │
│     → generates: tool call (fix the code)               │
│                                                         │
│  6. ... loop continues until done                       │
└─────────────────────────────────────────────────────────┘
```

Now the model can see — in real time — whether its code actually works. It wrote a function, the tests failed, the failure traceback is right there in the context, and it generates a fix. Then the tests run again. Then it sees the new result. Each iteration, it is pattern-matching against a richer, more specific input that includes *actual outcomes* from the real environment.

This is the same mechanism from Step 1 — pattern matching on input — but now the input includes live feedback from the real world. The model doesn't need to "reason" about whether its code is correct. It can *see* the test output and match against patterns it's seen a million times: "this traceback means this kind of bug, which is typically fixed by this kind of change."

## Putting It All Together

An LLM coding agent is not magic. It is a loop built from simple pieces:

| Layer | What it does | Why it matters |
|---|---|---|
| **LLM** | Generates the most likely output from its input | It has seen billions of lines of code — it knows the patterns |
| **Context control** | Shapes the input with examples, conventions, and instructions | Steers the model away from "average internet code" toward your standards |
| **Conversation history** | Replays the full conversation each turn | Creates the illusion of memory so the model stays coherent across a session |
| **Tool calling** | Lets the model emit structured actions instead of just text | Gives the system the ability to interact with the real world |
| **Feedback loop** | Feeds tool results back as input for the next turn | The model can observe real outcomes and self-correct |

Every "smart" behavior you see from a coding agent — writing code, running tests, reading errors, fixing bugs, iterating until things work — emerges from this loop. The model itself is doing the same thing every time: reading its input and generating the most probable output. The intelligence of the system comes from what we put in that input and how we close the loop.
