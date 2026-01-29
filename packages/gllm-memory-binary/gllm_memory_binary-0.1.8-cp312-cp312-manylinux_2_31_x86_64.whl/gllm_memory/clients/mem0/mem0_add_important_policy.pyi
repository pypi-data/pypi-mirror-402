from gllm_core.schema import Chunk
from gllm_memory.enums import MemoryMetadataCategory as MemoryMetadataCategory

class Mem0AddImportantPolicy:
    """Policy class for adding important metadata to memory chunks.

    This class is responsible for enriching memory chunks with important-related
    metadata based on the is_important flag.
    """
    @staticmethod
    def enrich_metadata(metadata: dict[str, str | None], is_important: bool) -> dict[str, str | None]:
        """Enrich metadata with important-related fields.

        Args:
            metadata (dict[str, str | None]): Original metadata dictionary to enrich.
            is_important (bool): Flag indicating if the memory is important.

        Returns:
            dict[str, str | None]: Enriched metadata with is_important and mark_important_at fields.
        """
    @staticmethod
    def update_important_metadata(existing_metadata: dict[str, str | None], is_important: bool) -> dict[str, str | None]:
        """Update existing metadata with important-related fields.

        This method handles updating importance metadata. When marking as important,
        it always sets a new timestamp. When marking as not important, it clears the timestamp.

        Args:
            existing_metadata (dict[str, str]): Existing metadata dictionary to update.
            is_important (bool): Flag indicating if the memory is important.

        Returns:
            dict[str, str]: Updated metadata with is_important and mark_important_at fields.
        """
    @staticmethod
    def get_nested_metadata_from_dict(metadata: dict | None, key: str) -> str | None:
        """Get metadata value from nested metadata dictionary.

        Args:
            metadata (dict | None): Metadata dictionary to extract from.
            key (str): Metadata key to retrieve.

        Returns:
            str | None: Metadata value or None if not found.
        """
    @staticmethod
    def sort_chunks_by_importance(chunks: list[Chunk]) -> list[Chunk]:
        """Sort chunks by importance priority.

        Important chunks are sorted first by mark_important_at (descending),
        followed by non-important chunks sorted by created_at (descending).

        Args:
            chunks (list[Chunk]): List of chunks to sort.

        Returns:
            list[Chunk]: Sorted list with important chunks first, then non-important chunks.
        """
    @staticmethod
    def validate_update_important_memory(is_currently_important: bool, new_content: str | None, metadata: dict[str, str] | None) -> tuple[bool, str | None]:
        """Validate if update to important memory is allowed.

        Important memories can only be unmarked (is_important=False).
        Content and metadata updates are blocked for important memories.

        Args:
            is_currently_important (bool): Whether memory is currently important.
            new_content (str | None): New content to update.
            metadata (dict[str, str] | None): New metadata to update.

        Returns:
            tuple[bool, str | None]: (is_allowed, reason). reason is None if allowed,
                otherwise contains explanation why update is blocked.
        """
    @staticmethod
    def filter_deletable_memories(memories: list[dict]) -> list[dict]:
        """Filter out important memories from a list of memories to delete.

        Important memories are protected and cannot be deleted. This method separates
        deletable from protected memories.

        Args:
            memories (list[dict]): List of memory dictionaries to filter.
                Each memory dict should have 'memory_id' and 'metadata' keys.

        Returns:
            list[dict]: Filtered list containing only deletable (non-important) memories.
        """
