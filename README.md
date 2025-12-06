# chain-reaction ⚡

My incremental journey learning to create agentic workflows with LangChain and LangGraph.

## About

Working through [Generative AI with LangChain](https://github.com/benman1/generative_ai_with_langchain) to build hands-on experience with:

- [x] [LangChain fundamentals](1-langchain-fundamentals/README.md)
- [ ] [LangGraph fundamentals](2-langgraph-fundamentals/README.md)
- [ ] Retrieval Augmented Generation (RAG)
- [ ] Functions, Tools and Agents
- [ ] Multi-agent systems
- [ ] Evaluation & Testing

Each concept gets its own directory with dedicated experiments and notes.

## Requirements

```plain
langchain>=1.0.0
```

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

---

*Learning in public, one chain at a time.* 🔗
