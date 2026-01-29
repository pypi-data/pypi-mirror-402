from _typeshed import Incomplete
from enum import StrEnum
from gllm_inference.schema import Message

Base: Incomplete

class Parameter:
    """Defines the method parameters for the chat history manager."""
    OPERATION: str
    CONVERSATION_ID: str
    ORGANIZATION_ID: str
    USER_MESSAGE_ID: str
    USER_MESSAGE: str
    USER_METADATA: str
    ASSISTANT_MESSAGE_ID: str
    ASSISTANT_MESSAGE: str
    ASSISTANT_METADATA: str
    PARENT_ID: str
    IS_ACTIVE: str
    SOURCE: str
    FEEDBACK: str
    PAIR_LIMIT: str
    LAST_MESSAGE_ID: str

class SchemaKey:
    """Defines the keys of the message schema in the database."""
    ID: str
    CONVERSATION_ID: str
    ORGANIZATION_ID: str
    ROLE: str
    CONTENT: str
    PARENT_ID: str
    CREATED_TIME: str
    UPDATED_TIME: str
    IS_ACTIVE: str
    METADATA: str
    FEEDBACK: str
    SOURCE: str
    ATTACHMENTS: str

class MessageModel(Base):
    '''An SQLAlchemy declarative base for the message table model.

    Attributes:
        id (String): Primary key for the message.
        conversation_id (String): Identifier for the conversation this message belongs to.
        organization_id (String): Identifier for the organization this message belongs to.
        role (String): Role of the entity sending the message (e.g., \'user\', \'assistant\').
        content (String): Actual content/text of the message.
        parent_id (String): Parent ID for the message.
        created_time (DateTime): Timestamp when the message was created.
        is_active (Boolean, optional): Whether the message is active. Defaults to True.
        feedback (String, optional): Feedback for the message. Defaults to None.
        source (String, optional): Source of the message. Defaults to None.
        metadata_ (String, optional): Metadata for the message. Defaults to "{}".
    '''
    __tablename__: str
    id: Incomplete
    conversation_id: Incomplete
    organization_id: Incomplete
    role: Incomplete
    content: Incomplete
    parent_id: Incomplete
    created_time: Incomplete
    is_active: Incomplete
    feedback: Incomplete
    source: Incomplete
    metadata_: Incomplete

class ConversationModel(Base):
    """An SQLAlchemy declarative base for the conversation table model.

    Attributes:
        id (String): Primary key for the conversation.
        user_id (String): User ID for the conversation.
        chatbot_id (String): Chatbot ID for the conversation.
        organization_id (String): Identifier for the organization this conversation belongs to.
        title (String): Title of the conversation.
        created_time (DateTime): Timestamp when the conversation was created.
        updated_time (DateTime): Timestamp when the conversation was updated.
        is_active (Boolean, optional): Whether the conversation is active. Defaults to True.
        is_anonymized (Boolean, optional): Whether the conversation is anonymized. Defaults to True.
        old_username (String, optional): Old username for the conversation. Defaults to None.
        metadata_ (String, optional): Metadata for the conversation. Defaults to None.
    """
    __tablename__: str
    id: Incomplete
    user_id: Incomplete
    chatbot_id: Incomplete
    organization_id: Incomplete
    title: Incomplete
    created_time: Incomplete
    updated_time: Incomplete
    is_active: Incomplete
    is_anonymized: Incomplete
    old_username: Incomplete
    metadata_: Incomplete

class OperationType(StrEnum):
    """The type of operation for the chat history manager.

    Attribute:
        RETRIEVE (str): The operation type for retrieving the chat history.
        STORE (str): The operation type for storing the chat history.
    """
    RETRIEVE: str
    STORE: str
MessagePair = tuple[Message, Message]
