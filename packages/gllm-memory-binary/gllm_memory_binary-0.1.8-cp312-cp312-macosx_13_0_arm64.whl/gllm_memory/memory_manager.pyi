from gllm_core.schema import Chunk
from gllm_inference.schema.message import Message as Message
from gllm_memory.builder.build_memory_client import build_from_env as build_from_env
from gllm_memory.clients.memory_client import BaseMemoryClient as BaseMemoryClient
from gllm_memory.enums import MemoryScope as MemoryScope

class MemoryManager:
    """Main memory manager that orchestrates the memory system.

    This class provides a platform-agnostic interface for memory operations,
    allowing users to work with the gllm_memory SDK without needing to know
    which memory platform is used internally.

    Attributes:
        _client (BaseMemoryClient): The underlying memory client instance.
    """
    def __init__(self, *, api_key: str, instruction: str | None = None, host: str | None = None) -> None:
        """Initialize the MemoryManager.

        Args:
            api_key (str): API key for authentication. Required for client initialization.
            instruction (str | None, optional): Custom instructions for memory handling.
                Defaults to None.
            host (str | None, optional): Host for the memory client.
                Defaults to None.

        Raises:
            RuntimeError: If client initialization fails due to invalid API key or configuration.
        """
    async def add(self, user_id: str, agent_id: str, messages: list[Message] = None, scopes: set[MemoryScope] = None, metadata: dict[str, str] = None, infer: bool = True, is_important: bool = False) -> list[Chunk]:
        """Add new memory items from a list of messages.

        Args:
            user_id (str): User identifier for the memory operation. Required.
            agent_id (str): Agent identifier for the memory operation. Required.
            messages (list[Message] | None, optional): List of messages to store in memory. Each message
                contains role, contents, and metadata information. Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to {MemoryScope.USER}.
            metadata (dict[str, str] | None, optional): Metadata to include with the memory.
                Defaults to None.
            infer (bool, optional): Whether to infer relationships. Defaults to True.
            is_important (bool, optional): Force all added memories to retain important status. Defaults to False.

        Returns:
            list[Chunk]: List of created memory chunks containing the stored memory data.

        Raises:
            Exception: If the operation fails due to client errors or invalid parameters.
        """
    async def search(self, query: str, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None, threshold: float | None = 0.3, top_k: int | None = 10, include_important: bool = False, rerank: bool = False) -> list[Chunk]:
        """Search memories using the memory provider.

        Args:
            query (str): Search query string. Required for memory retrieval.
            user_id (str | None, optional): User identifier for the memory operation.
                Defaults to None.
            agent_id (str | None, optional): Agent identifier for the memory operation.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to {MemoryScope.USER}.
            metadata (dict[str, str] | None, optional): Metadata filters to include with the memory.
                Defaults to None.
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
    async def list_memories(self, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None, keywords: str | list[str] | None = None, page: int = 1, page_size: int = 100) -> list[Chunk]:
        """List all memories for a given user identifier with pagination.

        Args:
            user_id (str | None, optional): User identifier for the memory operation.
                Defaults to None.
            agent_id (str | None, optional): Agent identifier for the memory operation.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to {MemoryScope.USER}.
            metadata (dict[str, str] | None, optional): Metadata filters to include with the memory.
                Defaults to None.
            keywords (str | list[str] | None, optional): Keywords to search for in memory content.
                Can be a single string or list of strings. Defaults to None.
            page (int, optional): Page number for pagination. Defaults to 1.
            page_size (int, optional): Number of items per page. Defaults to 100.

        Returns:
            list[Chunk]: List of retrieved memory chunks matching the specified criteria.

        Raises:
            Exception: If the operation fails due to client errors or invalid parameters.
        """
    async def delete(self, memory_ids: list[str] | None = None, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None) -> list[Chunk]:
        """Delete memories by IDs or by user identifier/scope.

        Args:
            memory_ids (list[str] | None, optional): List of memory ID UUID strings for ID-based deletion.
                If provided, only memories with these IDs will be deleted. Defaults to None.
            user_id (str | None, optional): User identifier for scope-based deletion.
                Used when deleting by user scope. Defaults to None.
            agent_id (str | None, optional): Agent identifier for scope-based deletion.
                Used when deleting by agent scope. Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for identifier-based deletion.
                Defines which memory scopes to target. Defaults to {MemoryScope.USER}.
            metadata (dict[str, str] | None, optional): Metadata filters to include with the deletion.
                Defaults to None.

        Returns:
            list[Chunk]: List of deleted memory chunks containing the removed memory data.
        """
    async def delete_by_user_query(self, query: str, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None, threshold: float | None = 0.3, top_k: int | None = 10) -> list[Chunk]:
        """Delete memories based on a query.

        Args:
            query (str): Search query string to identify memories to delete. Required.
            user_id (str | None, optional): User identifier for the memory operation.
                Used to scope the deletion operation. Defaults to None.
            agent_id (str | None, optional): Agent identifier for the memory operation.
                Used to scope the deletion operation. Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defines which memory scopes to target. Defaults to {MemoryScope.USER}.
            metadata (dict[str, str] | None, optional): Metadata filters to include with the deletion.
                Defaults to None.
            threshold (float | None, optional): Minimum similarity threshold for matching memories.
                Defaults to 0.3 (provider-specific default).
            top_k (int | None, optional): Maximum number of memories to delete.
                Defaults to 10 (provider-specific default).

        Returns:
            list[Chunk]: List of deleted memory chunks containing the removed memory data.

        Raises:
            Exception: If the operation fails due to client errors or invalid parameters.
        """
    async def update(self, memory_id: str, new_content: str | None = None, metadata: dict[str, str] | None = None, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, is_important: bool | None = None) -> Chunk:
        """Update an existing memory by ID.

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
            Chunk: The updated memory chunk containing the modified memory data.
            None: If the memory is not found or the operation fails.

        Raises:
            Exception: If the operation fails due to client errors or invalid parameters.
        """
