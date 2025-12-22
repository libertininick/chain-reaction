"""Configuration tools."""

from enum import StrEnum

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings


class APIKeys(BaseSettings, env_file=".env", env_file_encoding="utf-8"):
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

    Notes:
        - Anthropic models names: https://docs.claude.com/en/docs/about-claude/models/overview
    """

    CLAUDE_HAIKU = "claude-haiku-4-5-20251001"
    CLAUDE_SONNET = "claude-sonnet-4-5-20250929"
    CLAUDE_OPUS = "claude-opus-4-1-20250805"


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
