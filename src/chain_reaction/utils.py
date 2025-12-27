"""Utilities for the Chain Reaction project."""

from typing import Any

from langchain.messages import AnyMessage
from pydantic import BaseModel


def get_last_message(response: dict[str, Any]) -> AnyMessage | None:
    """Extract the last message from a response dictionary.

    Args:
        response (dict[str, Any]): A dictionary containing a list of messages under the key "messages".

    Returns:
        AnyMessage | None: The last message if available, otherwise None.
    """
    messages = response.get("messages", [])
    if messages:
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
        TypeError: If the structured response is not an instance of the expected model type.
    """
    structured_response = response.get("structured_response")
    if structured_response is not None and not isinstance(structured_response, model):
        raise TypeError(
            f"structured_response is not of the expected type: {model.__name__}; "
            f"got {type(structured_response).__name__} instead."
        )
    return structured_response
