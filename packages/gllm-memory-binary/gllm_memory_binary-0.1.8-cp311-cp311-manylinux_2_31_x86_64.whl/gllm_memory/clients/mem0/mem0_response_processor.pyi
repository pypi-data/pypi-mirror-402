from gllm_core.schema import Chunk
from gllm_memory.enums import MemoryOperationType as MemoryOperationType
from typing import Any

class Mem0ResponseProcessor:
    """Handles processing of Mem0 API responses into Chunk objects."""
    def __init__(self) -> None:
        """Initialize the response processor."""
    def process_add_response(self, result_or_results: dict[str, Any] | list[dict[str, Any]] | None) -> list[Chunk]:
        """Parse one or many Mem0 add responses into a flat list of Chunk.

        Args:
            result_or_results (dict[str, Any] | list[dict[str, Any]] | None): Raw add response(s).

        Returns:
            list[Chunk]: Flat list of created chunks.

        Raises:
            Exception: If response is None.
        """
    def process_retrieve_response(self, result: list[dict[str, Any]] | dict[str, Any] | str | None) -> list[Chunk]:
        """Process Mem0 retrieve/get_all response and convert to Chunk objects.

        Args:
            result (list[dict[str, Any]] | dict[str, Any] | str | None): Raw search/get_all response.

        Returns:
            list[Chunk]: Retrieved memory chunks.
        """
    def process_single_memory_response(self, mem0_response: dict[str, Any]) -> Chunk:
        """Process a single Mem0 memory response into a Chunk object.

        This method is specifically designed for update operations that return
        a single memory object rather than a list of results.

        Args:
            mem0_response (dict[str, Any]): Single Mem0 response object from update operation.

        Returns:
            Chunk: Normalized chunk with appropriate metadata.

        Raises:
            Exception: If response is not a valid memory object.
        """
