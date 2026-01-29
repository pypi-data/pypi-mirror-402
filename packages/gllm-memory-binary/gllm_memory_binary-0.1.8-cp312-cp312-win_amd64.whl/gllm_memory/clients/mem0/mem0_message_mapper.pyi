from gllm_inference.schema.message import Message as Message
from gllm_memory.schema import Mem0Message as Mem0Message

class Mem0MessageMapper:
    """Handles conversion of Message objects to Mem0-specific message format."""
    def __init__(self) -> None:
        """Initialize the message mapper."""
    def mapping_messages(self, messages: list[Message]) -> list[Mem0Message]:
        '''Map Message objects to Mem0-specific message format.

        This method converts Message objects to the format expected by Mem0 API.

        Args:
            messages (list[Message]): List of Message objects containing role, contents,
                and metadata information.

        Returns:
            list[Mem0Message]: List of Mem0-formatted message objects. Each object contains
                "role" and "content" fields as expected by Mem0.

        Raises:
            ValueError: If message content is invalid.
            TypeError: If message content is not a string.
            ValidationError: If Pydantic validation fails.
        '''
