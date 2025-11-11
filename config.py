"""Configuration for chain-reaction."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class APIKeys(BaseSettings, env_file=".env", env_file_encoding="utf-8"):
    """API keys for various LLM providers."""

    anthropic: SecretStr = Field(default=SecretStr(""), description="API key for Anthropic LLMs.")
    openai: SecretStr = Field(default=SecretStr(""), description="API key for OpenAI LLMs.")
