from _typeshed import Incomplete
from collections.abc import Callable
from gllm_memory.enums import MemoryScope as MemoryScope
from typing import Any

BOTH_SCOPES_LENGTH: int
BOTH_SCOPES_SET: Incomplete
FilterDict = dict[str, list[dict[str, Any]]]
FilterBuilder = Callable[[str | None, str | None], FilterDict | None]

class Mem0FilterStrategy:
    '''Handles strategy pattern for base filter determination.

    This class is responsible for determining the appropriate base filters
    based on user_id, agent_id, and scope combinations using the Strategy pattern.

    Each strategy is implemented as a named method for better:
    - Testability: Each method can be tested independently
    - Debuggability: Stack traces show method names, not "<lambda>"
    - Documentation: Each strategy can have detailed docstrings
    - Maintainability: Easy to locate and modify specific strategies
    '''
    def __init__(self) -> None:
        """Initialize the filter strategy.

        Builds a mapping of (mode, scope) combinations to their respective
        filter-building methods.
        """
    def get_base_filters(self, user_id: str | None, agent_id: str | None, scopes: set[MemoryScope] | None) -> FilterDict | None:
        """Get base filters based on user_id, agent_id, and scope combinations.

        Args:
            user_id (str | None): User identifier for the memory operation.
            agent_id (str | None): Agent identifier for the memory operation.
            scopes (set[MemoryScope] | None): Set of scopes for the operation.

        Returns:
            FilterDict | None: Base filters or None if no filters needed.

        Raises:
            None: Returns None for invalid inputs rather than raising exceptions.
        """
