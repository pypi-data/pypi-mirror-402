"""Persistent memory implementation for LangChain using Alchemyst AI."""

import time
from typing import Any, Dict, List

from alchemyst_ai import AlchemystAI
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


class AlchemystMemory(BaseChatMessageHistory):
    """Persistent chat history powered by Alchemyst AI.

    This class provides persistent conversation memory for LangChain applications
    using Alchemyst AI's context storage service.

    Args:
        api_key: Your Alchemyst AI API key
        session_id: Unique identifier for this conversation session
        group_name: Optional group name for organizing contexts (defaults to session_id)

    Example:
        >>> from alchemyst_langchain import AlchemystMemory
        >>> from langchain.chains import ConversationChain
        >>> from langchain_openai import ChatOpenAI
        >>>
        >>> memory = AlchemystMemory(
        ...     api_key="your-api-key",
        ...     session_id="user-123"
        ... )
        >>>
        >>> llm = ChatOpenAI(model="gpt-4o-mini")
        >>> chain = ConversationChain(llm=llm, memory=memory)
        >>>
        >>> response = chain.invoke({"input": "My name is Alice"})
        >>> # Later...
        >>> response = chain.invoke({"input": "What's my name?"})
        >>> # Response: "Your name is Alice"
    """

    def __init__(
        self,
        api_key: str,
        session_id: str,
        group_name: str | None = None,
    ) -> None:
        """Initialize AlchemystMemory.

        Args:
            api_key: Your Alchemyst AI API key
            session_id: Unique session identifier
            group_name: Optional group name (defaults to session_id)
        """
        super().__init__()
        self.client = AlchemystAI(api_key=api_key)
        self.session_id = session_id
        self.group_name = group_name or session_id

    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve historical messages from Alchemyst.

        Returns:
            List of BaseMessage objects (HumanMessage or AIMessage)
        """
        try:
            # Search for conversation history in this session
            response = self.client.v1.context.search(
                query="conversation history",
                scope="internal",
                body_metadata={"group_name": [self.group_name]},
            )

            messages = []
            contexts = getattr(response, "contexts", [])

            for context in contexts:
                content = getattr(context, "content", "")
                metadata = getattr(context, "metadata", {})
                role = metadata.get("role", "human")

                if role == "ai":
                    messages.append(AIMessage(content=content))
                else:
                    messages.append(HumanMessage(content=content))

            return messages

        except Exception as e:
            print(f"Error loading messages: {e}")
            return []

    def add_message(self, message: BaseMessage) -> None:
        """Store a message in Alchemyst context.

        Args:
            message: The message to store (HumanMessage or AIMessage)
        """
        role = "ai" if isinstance(message, AIMessage) else "human"

        try:
            self.client.v1.context.memory.add(
                session_id=self.session_id,
                contents=[
                    {
                        "content": message.content,
                        "metadata": {
                            "role": role,
                            "session_id": self.session_id,
                            "type": "text",
                        },
                    }
                ],
                metadata={"group_name": [self.group_name]},
            )
        except Exception as e:
            print(f"Error adding message: {e}")

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add multiple messages at once.

        Args:
            messages: List of messages to add
        """
        for message in messages:
            self.add_message(message)

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load conversation history for LangChain.

        Includes retry logic to handle indexing latency.

        Args:
            inputs: Dictionary containing current input

        Returns:
            Dictionary with "history" key containing formatted conversation
        """
        # Try up to 3 times to account for indexing latency
        for attempt in range(3):
            msgs = self.messages
            if msgs:
                history_str = "\n".join(
                    [
                        f"{'AI' if isinstance(m, AIMessage) else 'Human'}: {m.content}"
                        for m in msgs
                    ]
                )
                return {"history": history_str}

            # Wait before retry (but not on last attempt)
            if attempt < 2:
                time.sleep(2)

        return {"history": ""}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save conversation turn to memory.

        Args:
            inputs: Dictionary containing user input
            outputs: Dictionary containing AI output
        """
        input_str = inputs.get("input", "")
        output_str = outputs.get("output", "")

        if input_str:
            self.add_message(HumanMessage(content=input_str))
        if output_str:
            self.add_message(AIMessage(content=output_str))

    def clear(self) -> None:
        """Clear all memory for this session.

        Deletes all stored conversation history associated with this session_id.
        """
        try:
            self.client.v1.context.memory.delete(
                memory_id=self.session_id,
                organization_id="default",
            )
        except Exception as e:
            print(f"Error clearing memory: {e}")
