"""Utilities for the Chain Reaction project."""

import json
from collections.abc import Iterable
from typing import Any

from langchain.agents import AgentState
from langchain.messages import AnyMessage
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel

console = Console()


def format_message_content(message: AnyMessage) -> str:  # noqa: C901
    """Convert message content to displayable string.

    Args:
        message (AnyMessage): Message to format as a string.

    Returns:
        str: Formatted message content
    """
    parts = []
    tool_calls_processed = False

    # Handle main content
    if isinstance(message.content, str):
        parts.append(message.content)
    elif isinstance(message.content, list):
        # Handle complex content like tool calls (Anthropic format)
        for item in message.content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text":
                parts.append(item["text"])
            elif item.get("type") == "tool_use":
                parts.append(f"\n🔧 Tool Call: {item['name']}")
                parts.append(f"   Args: {json.dumps(item['input'], indent=2, ensure_ascii=False)}")
                parts.append(f"   ID: {item.get('id', 'N/A')}")
                tool_calls_processed = True
    else:
        parts.append(str(message.content))

    # Handle tool calls attached to the message (OpenAI format) - only if not already processed
    if not tool_calls_processed and hasattr(message, "tool_calls") and message.tool_calls:
        for tool_call in message.tool_calls:  # ty: ignore[not-iterable]
            parts.append(f"\n🔧 Tool Call: {tool_call['name']}")
            parts.append(f"   Args: {json.dumps(tool_call['args'], indent=2, ensure_ascii=False)}")
            parts.append(f"   ID: {tool_call['id']}")

    return "\n".join(parts)


def format_messages(messages: Iterable[AnyMessage]) -> None:
    """Format and display a list of messages with Rich formatting."""
    for m in messages:
        msg_type = m.__class__.__name__.replace("Message", "")
        content = format_message_content(m)

        if msg_type == "Human":
            console.print(Panel(content, title="🧑 Human", border_style="blue"))
        elif msg_type == "Ai":
            console.print(Panel(content, title="🤖 Assistant", border_style="green"))
        elif msg_type == "Tool":
            console.print(Panel(content, title="🔧 Tool Output", border_style="yellow"))
        else:
            console.print(Panel(content, title=f"📝 {msg_type}", border_style="white"))


def get_messages(response_or_state: dict[str, Any] | AgentState) -> list[AnyMessage]:
    """Extract messages from a response dictionary or agent state.

    Args:
        response_or_state (dict[str, Any] | AgentState): A response dictionary or agent state containing a list of
            messages under the key "messages".

    Returns:
        list[AnyMessage]: A list of messages extracted from the response or agent state.
    """
    return response_or_state.get("messages", [])


def get_last_message(response_or_state: dict[str, Any] | AgentState) -> AnyMessage | None:
    """Extract the last message from a response dictionary or agent state.

    Args:
        response_or_state (dict[str, Any] | AgentState): A response dictionary or agent state containing a list of
            messages under the key "messages".

    Returns:
        AnyMessage | None: The last message if available, otherwise None.
    """
    if messages := get_messages(response_or_state):
        return messages[-1]
    return None


def get_structured_response[T: BaseModel](response: dict[str, Any], model: type[T]) -> T | None:
    """Extract the structured response from a response dictionary.

    Args:
        response (dict[str, Any]): A dictionary containing a structured response under the key "structured_response".
        model (type[T]): The Pydantic model type to parse the structured response into.

    Returns:
        T | None: The structured response if available, otherwise None.

    Raises:
        RuntimeError: If no structured_response is found in the response.
        TypeError: If the structured response is not an instance of the expected model type.
    """
    # Extract structured response from the response dictionary
    structured_response = response.get("structured_response")
    if structured_response is None:
        raise RuntimeError("No structured_response found in the response.")

    # Check if the structured response is of the expected type
    if not isinstance(structured_response, model):
        raise TypeError(
            f"structured_response is not of the expected type: {model.__name__}; "
            f"got {type(structured_response).__name__} instead."
        )
    return structured_response
