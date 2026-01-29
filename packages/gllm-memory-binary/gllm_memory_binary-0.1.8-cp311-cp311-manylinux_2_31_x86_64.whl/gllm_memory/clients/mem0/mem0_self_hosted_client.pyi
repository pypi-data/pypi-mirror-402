import httpx
from _typeshed import Incomplete
from mem0.client.utils import api_error_handler
from typing import Any, Iterable

logger: Incomplete
DEFAULT_HOST: str
AUTH_TOKEN_PREFIX: str
MEM0_USER_ID_HEADER: str
API_ENDPOINT_MEMORIES: str
API_ENDPOINT_SEARCH: str
TELEMETRY_EVENT_INIT: str
SYNC_TYPE_ASYNC: str
TELEMETRY_KEY_SYNC_TYPE: str
TELEMETRY_KEY_BASE_URL: str
DEFAULT_OUTPUT_FORMAT: str
DEPRECATION_WARNING_MESSAGE: str
INSECURE_REDIRECT_ERROR_MESSAGE: str
API_KEY_MISSING_ERROR: str
ORG_PROJECT_ID_ERROR: str
SEARCH_IDENTIFIER_ERROR: str
GET_ALL_IDENTIFIER_ERROR: str
DELETE_IDENTIFIER_ERROR: str
DEFAULT_TIMEOUT: int
REDIRECT_STATUS_CODES: Incomplete

class AsyncSelfHostedMemoryClient:
    '''Async client for self-hosted Mem0 memory servers.

    This class provides direct HTTP API access to a self-hosted Mem0 memory server.
    It implements the core memory operations (add, search, list, delete) using REST API calls
    to a custom Mem0 deployment, rather than the cloud service.

    The client automatically handles authentication, identifier injection, and response processing.
    It supports flexible identifier management through direct parameters, filters, or default values.

    Attributes:
        user_email (str): User email from environment or default.
        default_user_id (Optional[str]): Default user ID for automatic injection.
        default_uid (Optional[str]): Default UID for automatic injection.
        default_agent_id (Optional[str]): Default agent ID for automatic injection.
        api_key (str): Mem0 API key for authentication.
        user_id (str): Computed user identifier for API headers.
        org_id (Optional[str]): Organization ID for multi-tenant deployments.
        project_id (Optional[str]): Project ID for multi-tenant deployments.
        async_client (httpx.AsyncClient): HTTP client for API requests.
        _base_url (str): Computed base URL for the API endpoint.

    Args:
        api_key (Optional[str]): Mem0 API key. Falls back to MEM0_API_KEY env var.
        host (Optional[str]): Host URL for self-hosted server. Defaults to "https://api.mem0.ai".
        org_id (Optional[str]): Organization ID for enterprise deployments.
        project_id (Optional[str]): Project ID for enterprise deployments.
        client (Optional[httpx.AsyncClient]): Custom HTTP client instance.
        api_prefix (str): API path prefix. Defaults to "".
        init_project (bool): Whether to initialize project (currently unused).
        default_user_id (Optional[str]): Default user ID. Falls back to MEM0_DEFAULT_USER_ID env var.
        default_uid (Optional[str]): Default UID for automatic injection.
        default_agent_id (Optional[str]): Default agent ID for automatic injection.

    Raises:
        ValueError: If API key is not provided via parameter or MEM0_API_KEY environment variable.

    Example:
        ```python
        client = AsyncSelfHostedMemoryClient(
            api_key="your-api-key",
            host="https://your-mem0-server.com",
            default_user_id="user123"
        )

        # Add memories
        result = await client.add(
            messages=[{"role": "user", "content": "Hello world"}],
            user_id="user123"
        )

        # Search memories
        results = await client.search(
            query="Hello",
            user_id="user123"
        )
        ```
    '''
    user_email: Incomplete
    default_user_id: Incomplete
    api_key: Incomplete
    user_id: Incomplete
    org_id: Incomplete
    project_id: Incomplete
    default_uid: Incomplete
    default_agent_id: Incomplete
    async_client: Incomplete
    def __init__(self, api_key: str | None = None, host: str | None = None, org_id: str | None = None, project_id: str | None = None, client: httpx.AsyncClient | None = None, *, api_prefix: str = '', default_user_id: str | None = None, default_uid: str | None = None, default_agent_id: str | None = None) -> None:
        '''Initialize the AsyncSelfHostedMemoryClient.

        Args:
            api_key (Optional[str]): Mem0 API key.
            host (Optional[str]): Host URL for self-hosted server.
            org_id (Optional[str]): Organization ID for enterprise deployments.
            project_id (Optional[str]): Project ID for enterprise deployments.
            client (Optional[httpx.AsyncClient]): Custom HTTP client instance.
            api_prefix (str): API path prefix. Defaults to "".
            default_user_id (Optional[str]): Default user ID.
            default_uid (Optional[str]): Default UID for automatic injection.
            default_agent_id (Optional[str]): Default agent ID for automatic injection.
        '''
    @api_error_handler
    async def add(self, messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
        '''Add new memories to the Mem0 server.

        Sends a POST request to the /memories endpoint with the provided messages and metadata.
        Automatically injects user/agent identifiers from parameters, filters, or defaults.

        Args:
            messages (list[dict[str, str]]): List of message dictionaries with \'role\' and \'content\' keys.
            **kwargs: Additional parameters including:
                - scopes (Optional[list[str]]): Memory scopes (e.g., ["user", "agent"]).
                - agent_id (Optional[str]): Agent identifier.
                - app_id (Optional[str]): Application identifier.
                - metadata (Optional[dict[str, Any]]): Additional metadata.
                - output_format (Optional[str]): API output format (auto-set to "v1.1").
                - version (Optional[str]): API version.
                - user_id (Optional[str]): User identifier (auto-injected if not provided).
                - uid (Optional[str]): Alternative user identifier.
                - filters (Optional[str|dict]): JSON filters to extract identifiers from.

        Returns:
            dict[str, Any]: API response containing created memory items.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
            ValueError: If required identifiers cannot be determined.

        Example:
            ```python
            result = await client.add(
                messages=[{"role": "user", "content": "Hello world"}],
                user_id="user123",
                scopes=["user"]
            )
            ```
        '''
    @api_error_handler
    async def search(self, query: str, **kwargs) -> list[dict[str, Any]]:
        '''Search for memories matching a query.

        Sends a POST request to the /search endpoint to find memories semantically similar
        to the query. Supports filtering by user/agent identifiers and various search parameters.

        Args:
            query (str): Search query string to match against memory content.
            **kwargs: Additional search parameters including:
                - top_k (Optional[int]): Maximum number of results to return.
                - threshold (Optional[float]): Similarity threshold (0.0-1.0).
                - version (Optional[str]): API version.
                - keyword (Optional[str]): Keyword-based filtering.
                - scopes (Optional[list[str]]): Memory scopes to search within.
                - filters (Optional[str|dict]): JSON filters for advanced filtering.
                - user_id (Optional[str]): User identifier (required if not in filters/defaults).
                - uid (Optional[str]): Alternative user identifier.
                - agent_id (Optional[str]): Agent identifier.
                - run_id (Optional[str]): Run identifier.
                - app_id (Optional[str]): Application identifier.

        Returns:
            list[dict[str, Any]]: List of matching memory items from the API response.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
            ValueError: If no valid user/agent identifier is provided.

        Example:
            ```python
            results = await client.search(
                query="machine learning",
                user_id="user123",
                top_k=5,
                threshold=0.7
            )
            ```
        '''
    @api_error_handler
    async def get_all(self, page: int | None = None, page_size: int | None = None, **kwargs) -> list[dict[str, Any]]:
        '''Retrieve all memories for specified identifiers with pagination.

        Sends a GET request to the /memories endpoint to list memories associated with
        the provided user/agent identifiers. Supports pagination and filtering.

        Args:
            page (Optional[int]): Page number for pagination (1-based). Defaults to None.
            page_size (Optional[int]): Number of items per page. Defaults to None.
            **kwargs: Additional filtering parameters including:
                - version (Optional[str]): API version.
                - keyword (Optional[str]): Keyword-based filtering.
                - scopes (Optional[list[str]]): Memory scopes to filter by.
                - filters (Optional[str|dict]): JSON filters for advanced filtering.
                - user_id (Optional[str]): User identifier (required if not in filters/defaults).
                - uid (Optional[str]): Alternative user identifier.
                - agent_id (Optional[str]): Agent identifier.
                - run_id (Optional[str]): Run identifier.
                - app_id (Optional[str]): Application identifier.

        Returns:
            list[dict[str, Any]]: List of memory items from the API response.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
            ValueError: If no valid user/agent identifier is provided.

        Example:
            ```python
            memories = await client.get_all(
                user_id="user123",
                page=1,
                page_size=50
            )
            ```
        '''
    @api_error_handler
    async def delete(self, memory_id: str | None = None, **kwargs) -> dict[str, Any] | list[dict[str, Any]]:
        '''Delete memories by ID or by identifier filters.

        Supports two deletion modes:
        1. Delete a specific memory by its ID
        2. Delete all memories matching the provided identifiers and filters

        Args:
            memory_id (Optional[str]): Specific memory ID to delete. If provided, other parameters are ignored.
            **kwargs: Parameters for bulk deletion including:
                - scopes (Optional[list[str]]): Memory scopes to delete from.
                - version (Optional[str]): API version.
                - filters (Optional[str|dict]): JSON filters for advanced filtering.
                - user_id (Optional[str]): User identifier (required for bulk delete if not in filters/defaults).
                - uid (Optional[str]): Alternative user identifier.
                - agent_id (Optional[str]): Agent identifier.
                - run_id (Optional[str]): Run identifier.
                - app_id (Optional[str]): Application identifier.

        Returns:
            dict[str, Any] | list[dict[str, Any]]: API response. For single deletions, returns deletion confirmation.
                For bulk deletions, returns list of deleted memory items.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
            ValueError: If no valid identifiers are provided for bulk deletion.

        Examples:
            ```python
            # Delete specific memory
            result = await client.delete(memory_id="mem_123")

            # Delete all memories for a user
            result = await client.delete(user_id="user123", scopes=["user"])
            ```
        '''
    @api_error_handler
    async def batch_delete(self, memory_ids: Iterable[dict[str, str]]) -> dict:
        '''Delete multiple memories by their IDs.

        Performs individual DELETE requests for each memory ID. This method handles
        the deletion sequentially and collects results/errors for each memory.

        Note: This implementation makes individual API calls for each memory ID rather
        than using a batch endpoint, as per the current Mem0 API design.

        Args:
            memory_ids (Iterable[dict]): Collection of memory dicts to delete.
                Each dict should have format: {"memory_id": "mem_123"}.

        Returns:
            dict: Deletion results containing:
                - deleted (int): Number of successfully deleted memories
                - ids (list[str]): List of all provided memory IDs
                - errors (list[dict]): List of errors for failed deletions, each containing:
                    - id (str): The memory ID that failed
                    - error (str): Error message

        Example:
            ```python
            result = await client.batch_delete([{"memory_id": "mem_123"}, {"memory_id": "mem_456"}])
            print(f"Deleted {result[\'deleted\']} memories")
            if result[\'errors\']:
                print(f"Errors: {result[\'errors\']}")
            ```
        '''
    @api_error_handler
    async def update(self, memory_id: str, text: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        '''Update an existing memory with new content.

        Sends a PUT request to the /memories/{memory_id} endpoint to update
        an existing memory with new content and metadata.

        Args:
            memory_id (str): ID of the memory to update.
            text (str | None = None): Updated text content of the memory. Defaults to None.
            metadata (Optional[dict[str, Any]]): Additional metadata to update. Defaults to None.
                This will be merged with existing metadata (new values override existing ones).

        Returns:
            dict[str, Any]: API response containing updated memory object with id, text, user_id,
                agent_id, app_id, run_id, hash, metadata, created_at, updated_at.

        Raises:
            httpx.HTTPStatusError: If the API request fails.

        Example:
            ```python
            # Update text only
            result = await client.update(
                memory_id="mem_123",
                text="Updated memory content"
            )

            # Update text and add new metadata
            result = await client.update(
                memory_id="mem_123",
                text="Updated memory content",
                metadata={"category": "example", "priority": "high"}
            )

            # Update text and modify existing metadata
            result = await client.update(
                memory_id="mem_123",
                text="Updated memory content",
                metadata={"category": "updated_category"}  # Overrides existing "category"
            )
            ```
        '''
    @api_error_handler
    async def get(self, memory_id: str) -> dict[str, Any]:
        """Get a memory by its ID.

        Args:
            memory_id (str): ID of the memory to get.

        Returns:
            dict[str, Any]: API response containing the memory object.
        """
