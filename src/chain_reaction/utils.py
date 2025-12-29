"""Utilities for the Chain Reaction project."""

from typing import Any

from langchain.agents import AgentState
from langchain.messages import AnyMessage
from pydantic import BaseModel


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
