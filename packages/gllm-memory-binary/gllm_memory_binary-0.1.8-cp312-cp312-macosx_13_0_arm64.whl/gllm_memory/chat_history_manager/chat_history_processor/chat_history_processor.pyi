from abc import ABC, abstractmethod
from gllm_memory.chat_history_manager.schema import MessagePair as MessagePair

class BaseChatHistoryProcessor(ABC):
    """An abstract base class for processing chat history.

    This class provides an interface for implementing different chat history filtering strategies.
    Subclasses should implement the `process` method to define specific filtering behavior.
    """
    @abstractmethod
    async def process(self, message_pairs: list[MessagePair], user_message: str) -> list[MessagePair]:
        """Filters the message pairs.

        This method must be implemented by the subclass to define the message pairs filtering logic.

        Args:
            message_pairs (list[MessagePair]): The message pairs to filter.
            user_message (str): The user message.

        Returns:
            list[MessagePair]: The filtered message pairs.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
