"""Configuration tools for API key management, LLM model selection, and model behavior presets.

Example usage:

Configure chat model
```python
from langchain.chat_models import init_chat_model
from chain_reaction.config import APIKeys, ModelBehavior, ModelName

# Load api keys from .env
api_keys = APIKeys()

# Initialize chat model with a given LLM and Behavior
model = init_chat_model(
    model=ModelName.CLAUDE_HAIKU,
    api_key=api_keys.anthropic,
    **ModelBehavior.factual().model_dump(),
)
```
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Final

from langchain.chat_models import BaseChatModel, init_chat_model
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings

CLAUDE_VERSION: Final[str] = "4-6"
GPT_VERSION: Final[str] = "5.4"


class APIKeys(BaseSettings, env_file=".env", env_file_encoding="utf-8", extra="ignore"):
    """API keys for various LLM providers and services.

    Attributes:
        anthropic (SecretStr): API key for Anthropic LLMs.
        openai (SecretStr): API key for OpenAI LLMs.
        tavily (SecretStr): API key for Tavily web searches.
    """

    anthropic: SecretStr = Field(default=SecretStr(""), description="API key for Anthropic LLMs.")
    openai: SecretStr = Field(default=SecretStr(""), description="API key for OpenAI LLMs.")
    tavily: SecretStr = Field(default=SecretStr(""), description="API key for Tavily web searches.")


class ModelName(StrEnum):
    """Enumeration of supported LLM model names.

    Attributes:
        CLAUDE_HAIKU: Anthropic Claude Haiku model.
        CLAUDE_SONNET: Anthropic Claude Sonnet model.
        CLAUDE_OPUS: Anthropic Claude Opus model.
        GPT_NANO: OpenAI GPT Nano model.
        GPT_MINI: OpenAI GPT Mini model.
        GPT: OpenAI GPT model.

    Notes:
        - Anthropic models: https://docs.claude.com/en/docs/about-claude/models/overview
        - OpenAI models: https://developers.openai.com/api/docs/models
    """

    CLAUDE_HAIKU = "claude-haiku-4-5"  # No 4-6 model yet
    CLAUDE_SONNET = f"claude-sonnet-{CLAUDE_VERSION}"
    CLAUDE_OPUS = f"claude-opus-{CLAUDE_VERSION}"
    GPT_NANO = f"gpt-{GPT_VERSION}-nano"
    GPT_MINI = f"gpt-{GPT_VERSION}-mini"
    GPT = f"gpt-{GPT_VERSION}"


class ModelBehavior(BaseModel):
    """Configuration for LLM model behavior.

    Attributes:
        temperature (float): Sampling temperature for response generation.
            Lower (0.0 - 0.3) for factual, higher (0.7 - 1.0) for creative.
            Defaults to 0.5.
        max_tokens (int): Maximum number of tokens in the generated response (1 - 4096). Defaults to 1024.
    """

    temperature: float = Field(default=0.5, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, ge=1, le=4096)

    @classmethod
    def creative(cls, max_tokens: int | None = None) -> ModelBehavior:
        """Create a ModelBehavior instance optimized for creative tasks.

        Args:
            max_tokens (int | None): Maximum number of tokens for the response.
                If None, maintains the default value.

        Returns:
            ModelBehavior: Instance with settings for creativity.
        """
        return cls(temperature=0.9, max_tokens=max_tokens or cls().max_tokens)

    @classmethod
    def deterministic(cls, max_tokens: int | None = None) -> ModelBehavior:
        """Create a ModelBehavior instance optimized for consistent responses, run to run.

        Useful for debugging and scenarios requiring consistent outputs.

        Args:
            max_tokens (int | None): Maximum number of tokens for the response.
                If None, maintains the default value.

        Returns:
            ModelBehavior: Instance with settings for deterministic responses.
        """
        return cls(temperature=0.0, max_tokens=max_tokens or cls().max_tokens)

    @classmethod
    def factual(cls, max_tokens: int | None = None) -> ModelBehavior:
        """Create a ModelBehavior instance optimized for factual tasks.

        Args:
            max_tokens (int | None): Maximum number of tokens for the response.
                If None, maintains the default value.

        Returns:
            ModelBehavior: Instance with settings for factual accuracy.
        """
        return cls(temperature=0.2, max_tokens=max_tokens or cls().max_tokens)


def get_chat_model(
    *,
    model_name: ModelName = ModelName.GPT_MINI,
    timeout: int | None = 60,
    max_retries: int = 2,
    temperature: float = 0.0,
    **kwargs: Any,
) -> BaseChatModel:
    """Initialize a chat model based on the specified model name and API keys.

    Args:
        model_name (ModelName): The name of the model to initialize. Defaults to ModelName.GPT_MINI.
        timeout (int | None, optional): Timeout for API requests in seconds. Defaults to 60 seconds.
        max_retries (int, optional): Maximum number of retries for API requests in case of failures. Defaults to 2.
        temperature (float, optional): Sampling temperature for the model. Defaults to 0.0.
        **kwargs (Any): Additional keyword arguments to pass to `init_chat_model`.

    Returns:
        BaseChatModel: A chat model instance initialized with the specified parameters.

    Raises:
        ValueError: If an unsupported model name is provided.

    """
    # Load API keys from .env file
    api_keys = APIKeys()

    # Get API key based on the model name
    match model_name:
        case ModelName.CLAUDE_HAIKU | ModelName.CLAUDE_SONNET | ModelName.CLAUDE_OPUS:
            api_key = api_keys.anthropic
        case ModelName.GPT_NANO | ModelName.GPT_MINI | ModelName.GPT:
            api_key = api_keys.openai
        case _:
            raise ValueError(f"Unsupported model name: {model_name}")

    # Initialize a chat model
    chat_model = init_chat_model(
        model=model_name.value,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
        temperature=temperature,
        **kwargs,
    )

    return chat_model
