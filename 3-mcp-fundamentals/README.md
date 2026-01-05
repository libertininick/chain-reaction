# MCP Fundamentals

The Model Context Protocol (MCP) is an open standard for connecting LLMs to external data sources, tools, and services through a unified interface.

## Client-server architecture
MCP follows a client-server architecture:

- **Servers** expose capabilities (tools, resources, prompts) via a standardized JSON-RPC protocol
- **Clients** (e.g. LangChain agents) connect to servers and invoke those capabilities
- **Transports** handle the communication layer (stdio for local processes, SSE/HTTP for remote)

## What Servers Can Expose

1. **Tools**: Functions the LLM can call (similar to LangChain tools, but protocol-standardized)
2. **Resources**: Data the LLM can read (files, database records, API responses)
3. **Prompts**: Reusable prompt templates with arguments

## FastMCP
FastMCP is a high-level Python framework that simplifies server creation with decorator-based syntax:

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def search_docs(query: str) -> str:
    """Search documentation."""
    # query implementations
    result = ...
    return result

@mcp.prompt()
def research_prompt(topic: str) -> str:
    """Generate a research prompt for a given topic."""
    return f"Research the following topic thoroughly: {topic}\nUse the search_docs tool to find relevant information."

if __name__ == "__main__":
    mcp.run()
```

#### FastMCP + Pydantic

With modern FastMCP (>= 2.0), idiomatic Python type annotations "just work". Specifically, you can define Pydantic models, use them as parameter and return types, and the framework handles schema generation, validation, and structured output automatically

**Automatic schema generation**: When you use a Pydantic model as a parameter or return type, FastMCP automatically generates the inputSchema / outputSchema from the model and includes it in the tool definition sent to clients.

```python
class BetaParameters(BaseModel):
    """Parameters of a Beta distribution."""

    alpha: float = Field(
        description=(
            "Alpha parameter of the Beta distribution, representing number of 'successes'. Must be greater than 0."
        ),
        gt=0,
    )
    beta: float = Field(
        description=(
            "Beta parameter of the Beta distribution, representing number of 'failures'. Must be greater than 0."
        ),
        gt=0,
    )
    
@mcp.tool
def calculate_confidence_interval(
    beta_params: BetaParameters,  # Schema auto-generated
    confidence_level: float = 0.95,
) -> ConfidenceInterval:
    ...
```

***Validation**: FastMCP uses Pydantic's flexible validation by default, coercing compatible inputs and validating the return of tool against the schema. For strict validation, use `FastMCP(strict_input_validation=True)`.


### LangChain Integration
LangChain has `langchain-mcp-adapters` which lets you connect to MCP servers and expose their tools to your agents. This means you can build tools once as MCP servers and use them across your LangGraph agents and any other MCP-compatible client.

```python
from langchain.agents import create_agent
from langchain_mcp_adapter.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

client = MultiServerMCPClient(
    {
        "docs": {
            "command": "python",
            "args": ["server.py"],
            "transport": "stdio",
        },
        # Configure additional server connections if needed
        ...
    }
)

# Get all tools from all servers, namespaced automatically
tools = client.get_tools()
    
# Create an agent with tools from MCP
agent = create_agent(model=..., tools=tools)
```

## MCP Server Examples
- [x] [Bayesian MCP Server & Agent](3-mcp-fundamentals/1-bayesian-tools/README.md)