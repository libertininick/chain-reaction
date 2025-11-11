"""Configuration for chain-reaction."""

from enum import StrEnum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class APIKeys(BaseSettings, env_file=".env", env_file_encoding="utf-8"):
    """API keys for various LLM providers."""

    anthropic: SecretStr = Field(default=SecretStr(""), description="API key for Anthropic LLMs.")
    openai: SecretStr = Field(default=SecretStr(""), description="API key for OpenAI LLMs.")


class ModelName(StrEnum):
    """Enumeration of supported LLM model names.

    Members:
        CLAUDE_HAIKU: Anthropic Claude Haiku model.
        CLAUDE_SONNET: Anthropic Claude Sonnet model.
        CLAUDE_OPUS: Anthropic Claude Opus model.

    Notes:
        - Anthropic models names: https://docs.claude.com/en/docs/about-claude/models/overview
    """

    CLAUDE_HAIKU = "claude-haiku-4-5-20251001"
    CLAUDE_SONNET = "claude-sonnet-4-5-20250929"
    CLAUDE_OPUS = "claude-opus-4-1-20250805"
