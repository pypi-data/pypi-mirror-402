from _typeshed import Incomplete
from gllm_core.schema import Chunk
from gllm_inference.schema.message import Message as Message
from gllm_memory.clients.mem0.mem0_add_important_policy import Mem0AddImportantPolicy as Mem0AddImportantPolicy
from gllm_memory.clients.mem0.mem0_chunk_creator import Mem0ChunkCreator as Mem0ChunkCreator
from gllm_memory.clients.mem0.mem0_filter_builder import Mem0FilterBuilder as Mem0FilterBuilder
from gllm_memory.clients.mem0.mem0_message_mapper import Mem0MessageMapper as Mem0MessageMapper
from gllm_memory.clients.mem0.mem0_response_processor import Mem0ResponseProcessor as Mem0ResponseProcessor
from gllm_memory.clients.mem0.mem0_self_hosted_client import AsyncSelfHostedMemoryClient as AsyncSelfHostedMemoryClient
from gllm_memory.clients.memory_client import BaseMemoryClient as BaseMemoryClient
from gllm_memory.clients.utils import dedupe_chunks as dedupe_chunks
from gllm_memory.enums import ApiVersion as ApiVersion, MemoryMetadataCategory as MemoryMetadataCategory, MemoryOperationType as MemoryOperationType, MemoryParameter as MemoryParameter, MemoryScope as MemoryScope, OutputFormat as OutputFormat
from gllm_memory.prompts.prompts import default_instruction_prompt as default_instruction_prompt
from gllm_memory.schema import GetMemoryParams as GetMemoryParams, Mem0AddParams as Mem0AddParams, SearchParams as SearchParams
from mem0 import AsyncMemoryClient
from typing import Any

class Mem0Client(BaseMemoryClient):
    """Mem0 Platform implementation of the BaseMemoryClient interface.

    This class implements the BaseMemoryClient interface using the Mem0 platform.
    It provides methods for adding, searching, updating, and deleting memories
    with proper scope handling and metadata management.

    Time-based filtering uses OR logic to ensure that either creation or modification
    timestamps fall within the specified time range. This provides flexible and
    intuitive behavior: memories are included if EITHER created_at OR updated_at
    is within the specified time range.

    Attributes:
        api_key (str): API key for Mem0 authentication.
        instruction (str): Custom instructions for memory handling. Uses default_instruction_prompt if not provided.
        timeout_sec (int): Timeout in seconds for API requests.
        host (str | None): Host URL for self-hosted Mem0 instance.
        app_id (str | None): Application ID from Mem0 project.
    """
    client: AsyncMemoryClient | None
    app_id: str | None
    instruction: Incomplete
    timeout_sec: Incomplete
    api_key: Incomplete
    host: Incomplete
    response_processor: Incomplete
    message_mapper: Incomplete
    filter_builder: Incomplete
    chunk_creator: Incomplete
    important_policy: Incomplete
    def __init__(self, *, api_key: str, instruction: str | None = None, timeout_sec: int = 30, host: str | None = None) -> None:
        """Initialize the Mem0 client.

        Args:
            api_key (str): API key for Mem0 authentication.
            instruction (str | None, optional): Custom instructions for memory handling.
                Defaults to default_instruction_prompt if not provided.
            timeout_sec (int, optional): Timeout in seconds for API requests. Defaults to 30.
            host (str | None, optional): Host URL for self-hosted Mem0 instance.
                Defaults to None.
        """
    async def add(self, user_id: str, agent_id: str, messages: list[Message] | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None, infer: bool = True, is_important: bool = False) -> list[Chunk]:
        """Add new memories from messages.

        Args:
            user_id (str): User identifier for the memory operation. Required.
            agent_id (str): Agent identifier for the memory operation. Required.
            messages (list[Message] | None, optional): List of messages to store in memory.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to {MemoryScope.USER}.
            metadata (dict[str, str] | None, optional): Metadata to include with the memory.
                Defaults to None.
            infer (bool, optional): Whether to infer relationships. Defaults to True.
            is_important (bool, optional): Flag indicating if the memory is important.
                Defaults to False.

        Returns:
            list[Chunk]: List of created memory chunks containing the stored memory data.

        Raises:
            Exception: If the operation fails due to client errors or invalid parameters.
        """
    async def search(self, query: str, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None, threshold: float | None = 0.3, top_k: int | None = 10, include_important: bool = False, rerank: bool = False) -> list[Chunk]:
        """Search memories by query, optionally including all important memories.

        Time-based filtering can be applied by including start_time and/or end_time in the metadata.
        The filtering uses OR logic to ensure that either created_at OR updated_at is within
        the specified time range, providing flexible and intuitive temporal filtering.

        Args:
            query (str): Search query string. Required.
            user_id (str | None, optional): User identifier for the memory operation.
                Defaults to None.
            agent_id (str | None, optional): Agent identifier for the memory operation.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to {MemoryScope.USER}.
            metadata (dict[str, str] | None, optional): Metadata filters for the search.
                Can include start_time and/or end_time for temporal filtering. Defaults to None.
            threshold (float | None, optional): Minimum similarity threshold for results.
                Defaults to 0.3.
            top_k (int | None, optional): Maximum number of results to return.
                Defaults to 10.
            include_important (bool, optional): If True, includes all important memories
                in addition to query matches. Results are deduplicated and sorted with
                important memories first. Defaults to False.
            rerank (bool, optional): If True, applies re-ranking to search results.
                Defaults to False.

        Returns:
            list[Chunk]: List of retrieved memory chunks matching the search criteria.
                If include_important=True, returns union of query matches and important memories.

        Raises:
            Exception: If the operation fails due to client errors or invalid parameters.
        """
    async def list_memories(self, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, Any] | None = None, keywords: str | list[str] | None = None, page: int = 1, page_size: int = 100) -> list[Chunk]:
        """List memories with pagination and filters.

        Time-based filtering can be applied by including start_time and/or end_time in the metadata.
        The filtering uses complex nested OR/AND structures to capture memories that were either
        created OR updated within the specified time range, ensuring comprehensive temporal coverage.

        Args:
            user_id (str | None, optional): User identifier for the memory operation.
                Defaults to None.
            agent_id (str | None, optional): Agent identifier for the memory operation.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to {MemoryScope.USER}.
            metadata (dict[str, Any] | None, optional): Metadata filters for the search.
                Can include start_time and/or end_time for temporal filtering. Defaults to None.
            keywords (str | list[str] | None, optional): Keywords to search for in memory content.
                Defaults to None.
            page (int, optional): Page number for pagination. Defaults to 1.
            page_size (int, optional): Number of items per page. Defaults to 100.

        Returns:
            list[Chunk]: List of retrieved memory chunks matching the specified criteria.

        Raises:
            Exception: If the operation fails due to client errors or invalid parameters.
        """
    async def delete(self, memory_ids: list[str] | None = None, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Delete memories by IDs or scope.

        Args:
            memory_ids (list[str] | None, optional): List of memory ID UUID strings for ID-based deletion.
                If provided, only memories with these IDs will be deleted. Defaults to None.
            user_id (str | None, optional): User identifier for scope-based deletion.
                Used when deleting by user scope. Defaults to None.
            agent_id (str | None, optional): Agent identifier for scope-based deletion.
                Used when deleting by agent scope. Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for identifier-based deletion.
                Defines which memory scopes to target. Defaults to {MemoryScope.USER, MemoryScope.ASSISTANT}.
            metadata (dict[str, Any] | None, optional): Metadata filters to include with the deletion.
                Defaults to None.

        Returns:
            list[Chunk]: List of deleted memory chunks containing the removed memory data.

        Raises:
            Exception: If the operation fails due to client errors or invalid parameters.
        """
    async def delete_by_user_query(self, query: str, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None, threshold: float | None = 0.3, top_k: int | None = 10) -> list[Chunk]:
        """Delete memories matching a query.

        Args:
            query (str): Search query string to identify memories to delete. Required.
            user_id (str | None, optional): User identifier for the memory operation.
                Used to scope the deletion operation. Defaults to None.
            agent_id (str | None, optional): Agent identifier for the memory operation.
                Used to scope the deletion operation. Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defines which memory scopes to target. Defaults to {MemoryScope.USER, MemoryScope.ASSISTANT}.
            metadata (dict[str, str] | None, optional): Metadata filters to include with the deletion.
                Defaults to None.
            threshold (float | None, optional): Minimum similarity threshold for matching memories.
                Defaults to 0.3.
            top_k (int | None, optional): Maximum number of memories to delete.
                Defaults to 10.

        Returns:
            list[Chunk]: List of deleted memory chunks containing the removed memory data.

        Raises:
            Exception: If the operation fails due to client errors or invalid parameters.
        """
    async def update(self, memory_id: str, new_content: str | None = None, metadata: dict[str, str] | None = None, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, is_important: bool | None = None) -> Chunk | None:
        """Update memory by ID.

        Args:
            memory_id (str): Unique identifier of the memory to update. Required.
            new_content (str | None, optional): Updated content for the memory.
                If None, the existing content remains unchanged. Defaults to None.
            metadata (dict[str, str] | None, optional): Updated metadata to merge or replace.
                Defaults to None.
            user_id (str | None, optional): User identifier for access control validation.
                Defaults to None.
            agent_id (str | None, optional): Agent identifier for access control validation.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the update operation.
                Defaults to {MemoryScope.USER, MemoryScope.ASSISTANT}.
            is_important (bool | None, optional): Flag indicating if the memory is important.
                If None, the existing is_important state remains unchanged. Defaults to None.

        Returns:
            Chunk | None: The updated memory chunk, or None if memory not found or operation fails.
        """
