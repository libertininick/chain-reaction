"""Science Fiction Writer Agent Example."""

import datetime

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

from chain_reaction.config import APIKeys, ModelBehavior, ModelName

# Load API keys from .env file
api_keys = APIKeys()

# Define the system prompt for the sci-fi writer agent
system_prompt = """
You are a science fiction writer, developing a rich, scientifically grounded
universe in the solar system in the 22nd century.

You will provide detailed information about the capitals of various celestial
bodies, including their history, culture, and economy.
"""


# Define the response schema
class CapitalInfo(BaseModel):
    """Information about the capital city of a celestial body."""

    capital: str = Field(description="The capital city of the given celestial body.")
    founded: datetime.date = Field(description="The date when the capital was founded.")
    population: int = Field(description="The population of the capital city.")
    description: str = Field(description="A brief description of the capital city.")
    primary_language: str = Field(description="The primary language spoken in the capital city.")
    core_industries: list[str] = Field(description="A list of core industries in the capital city.")
    brief_history: str = Field(description="A brief history of the capital city.")


# Initialize the creative chat model
creative_model = init_chat_model(
    model=ModelName.CLAUDE_HAIKU,
    timeout=None,
    max_retries=2,
    api_key=api_keys.anthropic,
    **ModelBehavior.creative().model_dump(),
)

# Create the sci-fi writer agent
agent = create_agent(
    model=creative_model,
    system_prompt=system_prompt,
    response_format=CapitalInfo,
)
