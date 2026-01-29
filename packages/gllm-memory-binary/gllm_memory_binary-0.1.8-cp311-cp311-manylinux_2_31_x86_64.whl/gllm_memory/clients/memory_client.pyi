from abc import ABC, abstractmethod
from gllm_core.schema import Chunk
from gllm_inference.schema.message import Message as Message
from gllm_memory.enums import MemoryScope as MemoryScope

class BaseMemoryClient(ABC):
    """Abstract interface for memory client implementations.

    This interface defines the contract that all memory clients must follow,
    making it easy to swap implementations without changing the rest of the code.
    """
    @abstractmethod
    async def add(self, user_id: str, agent_id: str, messages: list[Message] = None, scopes: set[MemoryScope] = None, metadata: dict[str, str] = None, infer: bool = True, is_important: bool = False) -> list[Chunk]:
        """Add new memory items from a list of messages.

        Args:
            user_id (str): User identifier for the memory operation. Required.
            agent_id (str): Agent identifier for the memory operation. Required.
            messages (list[Message] | None, optional): List of messages to store in memory. Each message
                contains role, contents, and metadata information. Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to [MemoryScope.USER].
            metadata (dict[str, str] | None, optional): Metadata to include with the memory.
                Defaults to None.
            infer (bool, optional): Whether to infer relationships. Defaults to True.
            is_important (bool, optional): Force all added memories to retain important status. Defaults to False.

        Returns:
            list[Chunk]: List of created memory chunks.

        Raises:
            Exception: If the operation fails.
        """
    @abstractmethod
    async def search(self, query: str, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None, threshold: float | None = 0.3, top_k: int | None = 10, include_important: bool = False, rerank: bool = False) -> list[Chunk]:
        """Search memories using the memory provider.

        Args:
            query (str): Search query string.
            user_id (str | None, optional): User identifier for the memory operation.
                Defaults to None.
            agent_id (str | None, optional): Agent identifier for the memory operation.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to {MemoryScope.USER}.
            metadata (dict[str, str] | None, optional): Metadata to include with the memory.
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
            list[Chunk]: List of retrieved memory chunks.

        Raises:
            Exception: If the operation fails.
        """
    @abstractmethod
    async def list_memories(self, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None, keywords: str | list[str] | None = None, page: int = 1, page_size: int = 100) -> list[Chunk]:
        """List all memories for a given user identifier.

        Optionally filtering the results by specific keywords.

        Args:
            user_id (str | None, optional): User identifier for the memory operation.
                Defaults to None.
            agent_id (str | None, optional): Agent identifier for the memory operation.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to {MemoryScope.USER}.
            metadata (dict[str, str] | None, optional): Metadata to include with the memory.
                Defaults to None.
            keywords (str | list[str] | None, optional): Keywords to search for in memory content.
                Defaults to None.
            page (int, optional): Page number for pagination. Defaults to 1.
            page_size (int, optional): Number of items per page. Defaults to 100.

        Returns:
            list[Chunk]: List of retrieved memory chunks.

        Raises:
            Exception: If the operation fails.
        """
    @abstractmethod
    async def delete(self, memory_ids: list[str] | None = None, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None) -> list[Chunk]:
        """Delete memories by IDs or by user identifier/scope.

        Args:
            memory_ids (list[str] | None, optional): List of memory ID UUID strings for ID-based deletion.
                Defaults to None.
            user_id (str | None, optional): User identifier for scope-based deletion.
                Defaults to None.
            agent_id (str | None, optional): Agent identifier for scope-based deletion.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for identifier-based deletion.
                Defaults to {MemoryScope.USER, MemoryScope.ASSISTANT}.
            metadata (dict[str, str] | None, optional): Metadata to include with the memory.
                Defaults to None.

        Returns:
            list[Chunk]: List of deleted memory chunks.

        Raises:
            ValueError: If neither memory_ids nor user_id/agent_id are provided.
        """
    @abstractmethod
    async def delete_by_user_query(self, query: str, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, metadata: dict[str, str] | None = None, threshold: float | None = 0.3, top_k: int | None = 10) -> list[Chunk]:
        """Delete memories based on a query.

        Args:
            query (str): Search query string to identify memories to delete.
            user_id (str | None, optional): User identifier for the memory operation.
                Defaults to None.
            agent_id (str | None, optional): Agent identifier for the memory operation.
                Defaults to None.
            scopes (set[MemoryScope] | None, optional): Set of scopes for the operation.
                Defaults to {MemoryScope.USER, MemoryScope.ASSISTANT}.
            metadata (dict[str, str] | None, optional): Metadata to include with the memory.
                Defaults to None.
            threshold (float | None, optional): Minimum similarity threshold for matching.
                Defaults to 0.3.
            top_k (int | None, optional): Maximum number of memories to delete.
                Defaults to 10.

        Returns:
            list[Chunk]: List of deleted memory chunks.

        Raises:
            Exception: If the operation fails.
        """
    @abstractmethod
    async def update(self, memory_id: str, new_content: str | None = None, metadata: dict[str, str] | None = None, user_id: str | None = None, agent_id: str | None = None, scopes: set[MemoryScope] | None = None, is_important: bool | None = None) -> Chunk | None:
        """Update an existing memory by ID.

        Args:
            memory_id (str): Unique identifier of the memory to update.
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
