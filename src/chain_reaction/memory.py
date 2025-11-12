"""Tools for chat and agent memory management."""

from uuid import UUID, uuid7

from langchain_core.chat_history import InMemoryChatMessageHistory
from pydantic import BaseModel, Field, validate_call


class ChatSessionHistoryManager(BaseModel):
    """Manages chat sessions with individual, in-memory message histories.

    Attributes:
        sessions (dict[UUID, InMemoryChatMessageHistory]): A mapping of session IDs to their chat histories.
        max_messages (int | None): Maximum number of messages to retain per session. If None, all messages are retained.
    """

    sessions: dict[UUID, InMemoryChatMessageHistory] = Field(default_factory=dict)
    max_messages: int | None = Field(default=None, description="Maximum number of messages to retain per session.")

    @validate_call
    def get_chat_history(self, session_id: UUID) -> InMemoryChatMessageHistory:
        """Get or create chat history for a given session ID.

        If the session ID does not exist, a new chat history will be created.

        Args:
            session_id (UUID): The unique identifier for the chat session.

        Returns:
            InMemoryChatMessageHistory: The chat history for the specified session.
        """
        # Retrieve the history for the session or create a new one
        chat_history = self.sessions.get(session_id, InMemoryChatMessageHistory())

        # Prune messages if necessary
        chat_history = self.prune_messages(chat_history)

        # Update the session's chat history
        self.sessions[session_id] = chat_history

        # Return the chat history for this session
        return chat_history

    def prune_messages(self, chat_history: InMemoryChatMessageHistory) -> InMemoryChatMessageHistory:
        """Prune older messages to enforce max_messages limit.

        Args:
            chat_history (InMemoryChatMessageHistory): The chat history to prune.

        Returns:
            InMemoryChatMessageHistory: The pruned chat history.
        """
        if self.max_messages is not None and len(chat_history.messages) > self.max_messages:
            chat_history.messages = chat_history.messages[-self.max_messages :] if self.max_messages > 0 else []
        return chat_history

    @staticmethod
    def create_session_config() -> dict[str, str]:
        """Create a new session configuration.

        Returns:
            dict[str, str]: A dictionary containing a new session ID.
        """
        return {"session_id": str(uuid7())}
