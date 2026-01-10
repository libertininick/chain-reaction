# Bayesian Beta-Binomial MCP Server

A Model Context Protocol (MCP) server that provides tools for Bayesian modeling using beta-binomial distributions. This server enables AI agents to help users estimate probabilities and update beliefs based on observed data.

## Overview

This MCP server exposes tools for beta-binomial Bayesian analysis, allowing users to:
- Express prior beliefs with varying conviction levels
- Update beliefs with observed data
- Calculate confidence intervals
- Sample outcomes from probability distributions

Built with [FastMCP](https://github.com/jlowin/fastmcp) (2.14.2), this server demonstrates how to create domain-specific tools that AI agents can use to solve real-world probabilistic problems.

## Server Tools

The server provides five core tools:

### 1. `get_beta_prior_from_beliefs`
Converts subjective beliefs into beta distribution parameters.
- **Inputs**: Prior probability (0-1), conviction level, optional adjustment factor
- **Conviction levels**: "random", "gut feeling", "educated guess", "reasonably confident", "very confident", "bet the farm"
- **Output**: Beta distribution parameters (alpha, beta)

### 2. `update_beta_parameters`
Updates beta distribution with new observed data using Bayesian updating.
- **Inputs**: Prior beta parameters, number of successes, number of failures
- **Output**: Updated beta distribution parameters

### 3. `calculate_confidence_interval`
Calculates confidence intervals for beta distributions.
- **Inputs**: Beta parameters, confidence level (default 0.95)
- **Output**: Lower and upper bounds of the interval

### 4. `sample_outcomes`
Draws random samples from a beta-binomial distribution.
- **Inputs**: Beta parameters, number of samples, optional random seed
- **Output**: Sample outcomes, probabilities, and summary statistics

### 5. `get_implied_sample_size`
Returns the implied sample size for each conviction level.
- **Inputs**: Conviction level, optional adjustment factor
- **Output**: Equivalent sample size for the conviction level

## Running the Server

Start the MCP server on port 8000:

```bash
uv run fastmcp run 3-mcp-fundamentals/1-bayesian-tools/server.py:mcp --transport http --port 8000
```

The server will be available at `http://localhost:8000/mcp` using the streamable HTTP transport protocol.

## Example Agent Usage

The [agent.ipynb](agent.ipynb) notebook demonstrates how to create a LangChain agent that uses this MCP server. The notebook shows:

### Setup
- Connecting to the MCP server using `MultiServerMCPClient`
- Retrieving tools and system prompt from the server
- Creating a LangChain agent with the tools

### Multi-Turn Conversation Example
The notebook walks through a complete Bayesian analysis workflow:

1. **Initial Question**: User asks about probability of rain tomorrow
2. **Prior Elicitation**: User provides initial belief (1% chance, gut feeling conviction)
3. **Data Update**: User adds historical data (37 rainy days out of 155 observed in January)
4. **Outcome Simulation**: Agent simulates possible outcomes for remaining days in the month

### Key Features Demonstrated
- **Asynchronous tool execution** using `ainvoke` (required for MCP tools)
- **Stateful conversations** with `InMemorySaver` checkpointer
- **Multi-step reasoning** where the agent chains multiple tool calls together
- **Natural language interaction** guided by the server's system prompt

## Use Cases

This server can help answer probabilistic questions such as:
- "What is the probability of rain tomorrow?"
- "How likely is it that my marketing campaign will succeed?"
- "What are the chances I'll get a year-end bonus at work?"

The beta-binomial model is particularly useful for binary outcomes (yes/no, success/failure) where you want to:
- Start with prior beliefs or intuition
- Update those beliefs as you gather data
- Quantify uncertainty with confidence intervals
- Make predictions about future outcomes

## Files

- [server.py](server.py) - FastMCP server implementation with tools and prompts
- [agent.ipynb](agent.ipynb) - Example notebook showing agent integration
