from gllm_memory.clients.utils import convert_to_utc_iso as convert_to_utc_iso
from typing import Any

class Mem0FilterEnhancer:
    """Handles filter enhancement operations for Mem0 search.

    This class is responsible for enhancing base filters with additional conditions
    such as metadata, app_id, keywords, and time-based filtering. It handles time
    range extraction and validation, using OR logic to ensure that either creation
    or modification timestamps fall within the specified time range.

    The OR filter structure ensures memories are included if EITHER created_at
    OR updated_at are within the specified time range, providing flexible and
    intuitive temporal filtering across search operations.
    """
    def __init__(self) -> None:
        """Initialize the filter enhancer."""
    def extract_time_range(self, metadata: dict | None) -> tuple[str | None, str | None]:
        '''Extract and validate start_time and end_time from metadata.

        Validates and converts time strings to UTC ISO-8601 Z format.
        The extracted time range will be used to filter memories by either created_at or updated_at fields.
        Supports partial time filtering (only start_time or only end_time).

        Supported formats:
        - "YYYY-MM-DD HH:mm:ss" (e.g., "2025-01-01 12:30:45")
        - "YYYY-MM-DD HH:mm" (e.g., "2025-01-01 12:30")
        - "YYYY-MM-DD" (e.g., "2025-01-01" -> matches entire day in UTC)
        - "HH:mm:ss" (e.g., "12:30:45")
        - ISO format with Z

        Args:
            metadata (dict | None): Metadata dictionary that may contain start_time and end_time fields.

        Returns:
            tuple[str | None, str | None]: Tuple of (start_time, end_time) in UTC ISO-8601 Z format.
                Returns (None, None) if metadata is None or both time fields are not provided.

        Raises:
            ValueError: If format is invalid or if start_time is greater than end_time (when both provided).

        Note:
            - Either start_time, end_time, or both can be provided independently.
            - Only start_time: filters memories where created_at OR updated_at >= start_time.
            - Only end_time: filters memories where created_at OR updated_at <= end_time.
            - Both: filters memories where created_at OR updated_at within the range [start_time, end_time].
            - Date-only format (e.g., "2025-01-01") matches the entire day in UTC timezone.
            - When both provided, start_time must be less than or equal to end_time.
            - Time filters use OR logic: memories match if EITHER created_at OR updated_at is within the time range.
        '''
    def enhance_filters(self, base_filters: dict[str, list[dict[str, Any]]] | None, metadata: dict[str, str] | None = None, app_id: str | None = None, keywords: str | list[str] | None = None, start_time: str | None = None, end_time: str | None = None) -> dict[str, list[dict[str, Any]]] | None:
        """Add metadata, app_id, keywords, and time filters to the base filters.

        Time filtering uses OR logic to ensure that either creation or modification
        timestamps fall within the specified time range. This provides flexible and
        intuitive behavior: memories are included if EITHER created_at OR updated_at
        is within the specified time range.

        Args:
            base_filters (dict[str, list[dict[str, Any]]] | None): Base filters from strategy.
            metadata (dict[str, str] | None): Additional metadata filters.
            app_id (str | None): Application identifier.
            keywords (str | list[str] | None): Keywords to search for.
            start_time (str | None): Start time in UTC ISO-8601 Z format for filtering.
                Uses gte (greater than or equal) condition when used alone.
            end_time (str | None): End time in UTC ISO-8601 Z format for filtering.
                Uses lte (less than or equal) condition when used alone.

        Returns:
            dict[str, list[dict[str, Any]]] | None: Enhanced filters or None if no base filters.
        """
