from enum import StrEnum

class MemoryProviderType(StrEnum):
    """Supported memory provider types.

    Attributes:
        MEM0 (str): Mem0 Platform provider.
    """
    MEM0: str

class ApiVersion(StrEnum):
    """Supported API versions for memory providers.

    Attributes:
        V2 (str): Version 2 of the API.
    """
    V2: str

class OutputFormat(StrEnum):
    """Supported output formats for memory providers.

    Attributes:
        V1_1 (str): Version 1.1 output format.
    """
    V1_1: str

class MemoryOperationType(StrEnum):
    """Supported memory operation types.

    Attributes:
        ADD (str): Add operation type.
        RETRIEVE (str): Retrieve operation type.
        DELETE (str): Delete operation type.
        UPDATE (str): Update operation type.
        UNKNOWN (str): Unknown operation type.
    """
    ADD: str
    DELETE: str
    UPDATE: str
    RETRIEVE: str
    UNKNOWN: str

class MemoryScope(StrEnum):
    """Supported memory operation scopes.

    Attributes:
        USER (str): User-specific memory operations.
        ASSISTANT (str): Assistant-specific memory operations.
    """
    USER: str
    ASSISTANT: str

class MemoryMetadataCategory(StrEnum):
    """Supported memory metadata categories.

    Attributes:
        USER_PREFERENCES (str): User preferences metadata category.
        SOURCE (str): Source metadata category.
        TARGET (str): Target metadata category.
        IS_IMPORTANT (str): Flag indicating if memory is important.
        MARK_IMPORTANT_AT (str): Timestamp when memory was marked as important.
    """
    USER_PREFERENCES: str
    SOURCE: str
    TARGET: str
    IS_IMPORTANT: str
    MARK_IMPORTANT_AT: str

class MemoryParameter(StrEnum):
    """Supported memory parameters.

    Attributes:
        APP_ID (str): App ID parameter.
        USER_ID (str): User ID parameter.
        AGENT_ID (str): Agent ID parameter.
        METADATA (str): Metadata parameter.
    """
    APP_ID: str
    USER_ID: str
    AGENT_ID: str
    METADATA: str
