from gllm_core.schema import Chunk
from typing import Any

class Mem0ChunkCreator:
    """Handles creating Chunk objects for Mem0 delete operations."""
    def __init__(self) -> None:
        """Initialize the chunk creator."""
    def create_deleted_chunks(self, filtered_memories: list[dict[str, Any]]) -> list[Chunk]:
        '''Create Chunk objects for deleted memories.

        Args:
            filtered_memories (list[dict[str, Any]]): List of filtered memory dicts
                containing keys "memory_id" and "content".

        Returns:
            list[Chunk]: List of Chunk objects indicating deleted memories.
        '''
