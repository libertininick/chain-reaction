"""Utilities for the Chain Reaction project."""

from typing import Any

from langchain.messages import AnyMessage


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
