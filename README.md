# chain-reaction ⚡

My incremental journey learning to create agentic workflows with LangChain and LangGraph.

## About

Working through [Generative AI with LangChain](https://github.com/benman1/generative_ai_with_langchain) to build hands-on experience with:

- [x] [LangChain](1-langchain-fundamentals/README.md)
- [ ] [LangGraph](2-langgraph-fundamentals/README.md)
- [ ] [Model Context Protocol](3-mcp-fundamentals/README.md)
- [ ] Evaluation & Testing


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
&& uv lock --upgrade \
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
