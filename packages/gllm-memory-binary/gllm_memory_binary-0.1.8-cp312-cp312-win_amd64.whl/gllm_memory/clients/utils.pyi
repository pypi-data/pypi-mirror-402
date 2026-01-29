from collections.abc import Iterable
from gllm_core.schema import Chunk
from gllm_memory.clients.constants import DATETIME_FULL_LENGTH as DATETIME_FULL_LENGTH, DATETIME_NO_SEC_LENGTH as DATETIME_NO_SEC_LENGTH, DATE_ONLY_LENGTH as DATE_ONLY_LENGTH, PEPPER as PEPPER, TIME_ONLY_LENGTH as TIME_ONLY_LENGTH

def convert_to_utc_iso(time_str: str | None, is_end_time: bool = False) -> str | None:
    '''Convert time string to UTC ISO-8601 Z format.

    Supports multiple flexible formats:
    - Full: "YYYY-MM-DD HH:mm:ss" (e.g., "2025-01-01 12:30:45")
    - No seconds: "YYYY-MM-DD HH:mm" (e.g., "2025-01-01 12:30" -> assumes :00 seconds)
    - Date only: "YYYY-MM-DD" (e.g., "2025-01-01" -> start: 00:00:00, end: 23:59:59 UTC)
    - Time only: "HH:mm:ss" (e.g., "12:30:45" -> assumes today\'s date)
    - ISO format: "YYYY-MM-DDTHH:mm:ssZ" or "YYYY-MM-DDTHH:mm:ss+00:00" (UTC only)

    All input times are treated as UTC. Non-UTC timezones will be rejected.

    Args:
        time_str (str | None): Time string to convert. Must be in UTC or naive (no timezone).
        is_end_time (bool, optional): If True, use 23:59:59 for date-only format. Defaults to False.

    Returns:
        str | None: UTC ISO-8601 Z formatted string (e.g., "2025-01-01T00:00:00Z") or None if invalid.
    '''
def hash_text(text: str) -> str:
    """Hash a text string using HMAC-SHA256 with salt and pepper.

    This function creates a deterministic hash from the input string for enhanced security
    and consistent identification.

    Security Features:
    - HMAC-SHA256 for authenticated hashing
    - Deterministic salt for consistent retrieval
    - Static pepper for application-level security

    Args:
        text (str): The string to be hashed.

    Returns:
        str: The HMAC-SHA256 hash of the input string.

    Raises:
        Exception: If the hashing fails.
    """
def dedupe_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """Dedupe chunks by stable key.

    Prefer higher score when duplicates appear.

    Args:
        chunks (list[Chunk]): List of chunks to deduplicate.

    Returns:
        list[Chunk]: Deduplicated list of chunks, sorted by score descending.
    """
def merge_and_dedupe_chunks(*chunk_lists: Iterable[Chunk] | None) -> list[Chunk]:
    """Merge and dedupe chunks.

    Args:
        *chunk_lists: One or more iterable containing Chunk (list, tuple, or generator).
            None values will be ignored.

    Returns:
        list[Chunk]: One list of merged chunks that has been deduplicated.
    """
