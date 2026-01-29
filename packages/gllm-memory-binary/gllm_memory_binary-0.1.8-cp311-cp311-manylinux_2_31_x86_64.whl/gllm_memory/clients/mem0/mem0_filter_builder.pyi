from gllm_memory.clients.mem0.mem0_filter_enhancer import Mem0FilterEnhancer as Mem0FilterEnhancer
from gllm_memory.clients.mem0.mem0_filter_strategy import Mem0FilterStrategy as Mem0FilterStrategy
from gllm_memory.enums import MemoryScope as MemoryScope
from typing import Any

class Mem0FilterBuilder:
    """Orchestrates filter building for Mem0 search operations.

    This class acts as a facade that coordinates between:
    - Mem0FilterStrategy: Determines base filters using strategy pattern
    - Mem0FilterEnhancer: Enhances base filters with metadata, app_id, keywords, time filters

    Time filtering uses OR logic to ensure that either creation or modification
    timestamps fall within the specified time range, providing flexible and
    intuitive temporal filtering across all search operations.
    """
    def __init__(self) -> None:
        """Initialize the filter builder."""
    def extract_time_range(self, metadata: dict | None) -> tuple[str | None, str | None]:
        """Extract and validate start_time and end_time from metadata.

        Delegates to Mem0FilterEnhancer for extraction and validation.

        Args:
            metadata (dict | None): Metadata dictionary that may contain start_time and end_time fields.

        Returns:
            tuple[str | None, str | None]: Tuple of (start_time, end_time) in UTC ISO-8601 Z format.

        Raises:
            ValueError: If validation fails (missing fields, invalid format, start_time > end_time).
        """
    def build_search_filters(self, user_id: str | None, agent_id: str | None, scopes: set[MemoryScope] | None, metadata: dict[str, str] | None = None, app_id: str | None = None, keywords: str | list[str] | None = None) -> dict[str, list[dict[str, Any]]] | None:
        """Build search filters based on user_id, agent_id, and scope combinations.

        Orchestrates filter building by:
        1. Getting base filters from strategy (based on user_id, agent_id, scopes)
        2. Extracting time range from metadata
        3. Enhancing base filters with metadata, app_id, keywords, time filters

        Time filtering uses OR logic to ensure that either creation or modification
        timestamps fall within the specified time range. This provides flexible and
        intuitive behavior: memories are included if EITHER created_at OR updated_at
        is within the specified time range.

        Args:
            user_id (str | None): User identifier for the memory operation.
            agent_id (str | None): Agent identifier for the memory operation.
            scopes (set[MemoryScope] | None): Set of scopes for the operation.
            metadata (dict[str, str] | None, optional): Additional metadata filters. Can contain
                start_time and end_time fields for time-based filtering using OR logic.
            app_id (str | None, optional): Application identifier.
            keywords (str | list[str] | None, optional): Keywords to search for in memories.

        Returns:
            dict[str, list[dict[str, Any]]] | None: Search filters or None if no filters needed.
        """
