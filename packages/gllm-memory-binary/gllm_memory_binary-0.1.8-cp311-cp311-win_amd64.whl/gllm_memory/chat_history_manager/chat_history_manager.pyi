from _typeshed import Incomplete
from gllm_core.schema import Component
from gllm_datastore.sql_data_store.sql_data_store import BaseSQLDataStore
from gllm_inference.schema import Message
from gllm_memory.chat_history_manager.chat_history_processor.chat_history_processor import BaseChatHistoryProcessor as BaseChatHistoryProcessor
from gllm_memory.chat_history_manager.schema import ConversationModel as ConversationModel, MessageModel as MessageModel, MessagePair as MessagePair, OperationType as OperationType, SchemaKey as SchemaKey
from typing import Any

DEFAULT_PAIR_LIMIT: int
MESSAGE_TUPLE_LENGTH: int
TARGET_COLUMNS: Incomplete

class ChatHistoryManager(Component):
    """A class for managing chat history in Gen AI applications.

    This class provides functionality for storing and retrieving chat history
    with optional processing via a ChatHistoryProcessor.

    Currently, this module only supports storing chat history in SQL databases.
    Database interactions are handled through the SQLAlchemy ORM via the SQLAlchemyDataStore class.

    Attributes:
        data_store (BaseSQLDataStore): Data store for storing and retrieving chat history.
        order_by (str): The column to order the chat history by.
        processor (BaseChatHistoryProcessor): Processor for chat history transformation.
        fallback_to_original_history (bool): Whether to fallback to the original history if the history
            processing fails or returns an empty list.
    """
    data_store: Incomplete
    order_by: Incomplete
    processor: Incomplete
    fallback_to_original_history: Incomplete
    def __init__(self, data_store: BaseSQLDataStore, order_by: str = ..., processor: BaseChatHistoryProcessor | None = None, fallback_to_original_history: bool = True) -> None:
        '''Initialize the chat history manager.

        Args:
            data_store (BaseSQLDataStore): Data store for storing and retrieving chat history. Currently only supports
                SQL-based data store.
            order_by (str, optional): The column to order the chat history by. Defaults to "created_time".
            processor (BaseChatHistoryProcessor | None, optional): Processor for chat history transformation.
                Defaults to None.
            fallback_to_original_history (bool, optional): Whether to fallback to the original history if the history
                processing fails or returns an empty list. Defaults to True.
        '''
    async def retrieve(self, conversation_id: str, organization_id: str, user_message: str | None = None, pair_limit: int = ..., last_message_id: str | None = None) -> list[Message]:
        """Retrieves the chat history of a given conversation ID.

        This method returns the chat history in the format of a list of Message.

        Args:
            conversation_id (str): The ID of the conversation.
            organization_id (str): The ID of the organization.
            user_message (str | None, optional): The user message. Defaults to None.
            pair_limit (int, optional): The number of user-assistant message pairs to retrieve.
                Defaults to DEFAULT_PAIR_LIMIT.
            last_message_id (str | None, optional): The ID of the last message to be retrieved in case of branching.
                Defaults to None, in which case the most recent message will be used as the last message.

        Returns:
            list[Message]: The retrieved and processed chat history.
        """
    async def store(self, conversation_id: str, organization_id: str, user_message: str, assistant_message: str, user_message_id: str | None = None, assistant_message_id: str | None = None, parent_id: str | None = None, is_active: bool = True, feedback: str | None = None, source: str | None = None, user_metadata: dict[str, Any] | None = None, assistant_metadata: dict[str, Any] | None = None) -> None:
        """Stores the chat history of a given conversation ID.

        Args:
            conversation_id (str): The ID of the conversation.
            organization_id (str): The ID of the organization.
            user_message (str): The user message.
            assistant_message (str): The assistant message.
            user_message_id (str | None, optional): The ID of the user message. Defaults to None,
                in which case a new UUID will be generated.
            assistant_message_id (str | None, optional): The ID of the assistant message. Defaults to None,
                in which case a new UUID will be generated.
            parent_id (str | None, optional): The parent ID of the user message. Defaults to None, in which case the
                conversation ID will be used as the parent ID.
            is_active (bool, optional): Whether the message is active. Defaults to True.
            feedback (str | None, optional): The feedback for the assistant message. Defaults to None.
            source (str | None, optional): The source of the assistant message. Defaults to None.
            user_metadata (dict[str, Any] | None, optional): Additional data to store for the user message.
                Defaults to None.
            assistant_metadata (dict[str, Any] | None, optional): Additional data to store for the assistant message.
                Defaults to None.
        """
    async def update(self, conversation_id: str, message_id: str, content: str | None = None, is_active: bool | None = None, feedback: str | None = None, source: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        """Updates an existing message in the chat history.

        Args:
            conversation_id (str): The ID of the conversation.
            message_id (str): The ID of the message to update.
            content (str | None, optional): The new content for the message. Defaults to None.
            is_active (bool | None, optional): Whether the message is active. Defaults to None.
            feedback (str | None, optional): The feedback for the message. Defaults to None.
            source (str | None, optional): The source of the message. Defaults to None.
            metadata (dict[str, Any] | None, optional): Additional data to store for the message.
                Defaults to None.
        """
