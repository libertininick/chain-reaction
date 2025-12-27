"""Interfaces and tools for managing agent state and context."""

from typing import Annotated

from langchain.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import Field


class MessageStateMixin:
    """Mixin to add message history to agent state.

    Attributes:
        messages (Annotated[list[AnyMessage], add_messages]): List of chat messages in the conversation.

    Examples:
        >>> from pydantic import BaseModel, Field

        Define a custom state model with message history:
        >>> class CustomState(BaseModel, MessageStateMixin):
        ...    some_attribute: str = Field(default="example", description="An example attribute")

    """

    messages: Annotated[list[AnyMessage], add_messages] = Field(
        default_factory=list, description="Chat messages in the conversation"
    )
