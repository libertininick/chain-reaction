# chain-reaction ⚡

My incremental journey learning to create agentic workflows with LangChain and LangGraph.

## About

Working through [DeepLearning.AI's LangChain courses](https://www.deeplearning.ai/courses/?courses_date_desc%5Bquery%5D=LangChain) to build hands-on experience with:
- [ ] [LangChain fundamentals](https://www.deeplearning.ai/short-courses/langchain-for-llm-application-development/)
- [ ] [Retrieval Augmented Generation (RAG)](https://www.deeplearning.ai/short-courses/langchain-chat-with-your-data/)
- [ ] [Functions, Tools and Agents](https://www.deeplearning.ai/short-courses/functions-tools-agents-langchain/)
- [ ] [AI Agents in LangGraph](https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/)
- [ ] [Long-Term Agentic Memory](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/)

Each course or concept gets its own directory with dedicated experiments and notes.

## Setup

Using `uv` for Python environment management:
```bash
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
   ```bash
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
```bash
uv run pre-commit run --all-files
```

---

*Learning in public, one chain at a time.* 🔗
