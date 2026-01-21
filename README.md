# chain-reaction ⚡

My incremental journey learning to create agentic workflows with LangChain, LangGraph, and FastMCP.

- **LangChain**: LangChain provides the building blocks for large language models (LLM) applications. It's a library of modular components like prompt templates, output parsers, memory systems, and tool integrations that can be composed together.

- **LangGraph**: LangGraph is a framework built on top of LangChain for creating stateful, agentic workflows. Workflows are defined as a graph of nodes and edges. Nodes represent different steps or agents and edges represent the flow between them. LangGraph is useful for building complex LLM applications that need to maintain state, handle cycles, support human-in-the-loop interactions, or coordinate multiple agents working together.

- **FastMCP**: The Model Context Protocol (MCP) is an open standard for connecting LLMs to external data sources, tools, and services through a unified interface. FastMCP is a high-level Python framework that simplifies MCP server creation with decorator-based syntax.

## Journey

### 🔗 LangChain & LangGraph fundamentals
  - [x] [Prompts and responses](notebooks/fundamentals/prompts-and-responses.ipynb)
  - [x] [Intro to chains and LangChain Expression Language (LCEL)](notebooks/fundamentals/intro-to-chains.ipynb)
  - [x] [A simple LangGraph graph](notebooks/fundamentals/simple-graph.ipynb)
  - [x] [Create an agent](notebooks/fundamentals/create-an-agent.ipynb)
  - [x] [Mock SciFi Writer Agent + LangSmith Studio example](agents/scifi_writer.py)
  - [x] [Locally running (private) agent with Ollama](notebooks/fundamentals/ollama-agent.ipynb)

### 🔗 Agent tools
  - [x] [Agent tools](notebooks/tools/agent-tools.ipynb)
  - [x] [ReAct agent in LangGraph](notebooks/tools/react-agent-graph.ipynb)
  - [x] [Caching tool calls locally](notebooks/tools/cache-tool-calls.ipynb)
  - [x] [Limiting number of tool calls with recursion limits](notebooks/tools/recusion-limits.ipynb)
  - [x] [Dynamic tool filtering based on context](notebooks/tools/context-based-tools.ipynb)
  - [x] [SQL toolkit for agent](notebooks/tools/sql-agent.ipynb)
  - [ ] [Polars DataFrame toolkit for agent](notebooks/tools/dataframe-agent.ipynb)

### 🔗 MCP
  - [x] [Bayesian tools MCP server](mcp-servers/bayesian-tools/README.md)

### 🔗 Memory, context, & state
  - [x] [Short-term memory for chat conversations & agents](notebooks/memory-context-state/short-term-memory.ipynb)
  - [x] [Agent context and state](notebooks/memory-context-state/context-and-state.ipynb)
  - [x] [Managing long conversations](notebooks/memory-context-state/managing-long-conversations.ipynb)

### 🔗 Human-in-the-loop
  - [x] [Human-in-the-loop](notebooks/human-in-the-loop.ipynb)

### 🔗 Multi-agent
  - [x] [Multi-agent systems](notebooks/multi-agent-systems.ipynb)


## Setup

Using `uv` for Python environment management:
```sh
# Clone repository
git clone git@github.com:libertininick/chain-reaction.git
cd chain-reaction

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Configure API keys
cp template.env .env
# Edit .env and add your API keys

# Set up pre-commit hooks
uv run pre-commit install
```

### API Keys

This project requires an Anthropic or OpenAI API key:

1. **Get your API key**:
2. **Configure your environment**: Copy `template.env` to `.env` and add your key:
   ```sh
   cp template.env .env
   ```
3. **Edit `.env`**: Replace `<your api key here>` with your actual API key

The `.env` file is gitignored to keep your API keys secure.

### Verify Your Setup

After completing the setup steps, run the [getting-started.ipynb](getting-started.ipynb) notebook to verify:
1. Dependencies are installed correctly
2. API key(s) are configured properly
3. You can successfully generate responses from a chat model

The notebook demonstrates a simple LangChain workflow using ChatAnthropic to generate a poem.

### LangSmith Studio

0. Create LangSmith API key and add to `.env` file

   ```plain
   LANGSMITH_API_KEY="<your api key here>"
   ```

1. Create an agent file: `some_agent.py`

   ```python
   from langchain.agents import create_agent
   from langchain.chat_models import init_chat_model

   # Initialize model
   chat_model = init_chat_model(...)

   # Create an agent
   agent = create_agent(
      model=creative_model,
      ...
   )
   ```

2. Configure [`langgraph.json`](langgraph.json)

   ```json
   {
      "dependencies": ["."],
      "graphs": {
         "<some agent>": "path/to/some_agent.py:agent"
      },
      "env": "./.env"
   }
   ```

2. Run LangSmith Studio

   ```sh
   uv run langgraph dev
   ```

### Development Tools

This project uses pre-commit hooks managed via `uv` to maintain code quality:
- **ruff**: Linting and formatting
- **pydoclint**: Docstring validation
- **nbstripout**: Strip Jupyter notebook outputs
- **ty**: Type checking

All tools run automatically on commit. To run manually:
```sh
uv run pre-commit run --all-files
```

### Updating dependencies

#### Update a single dependency

```sh
uv lock --upgrade-package <package name>
uv pip show <package name>
```

#### Update uv tool and all dependencies

1. Update `uv` tool
2. Upgrade `Python` version installed by `uv`
3. Upgrade all dependencies in `uv.lock` file
4. Sync virtual environment with updated dependencies
5. Prune `uv` cache to remove dependencies that are no longer needed

```sh
uv self update \
&& uv python upgrade \
&& uv lock --upgrade --exclude-newer "1 week" \
&& uv sync \
&& uv cache prune
```

### Update pre-commit hooks:

```sh
uv run pre-commit install-hooks \
&& uv run pre-commit autoupdate
```

---

*Learning in public, one chain at a time.* 🔗
