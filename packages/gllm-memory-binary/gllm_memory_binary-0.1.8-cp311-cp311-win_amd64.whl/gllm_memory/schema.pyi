from _typeshed import Incomplete
from gllm_memory.enums import ApiVersion as ApiVersion, OutputFormat as OutputFormat
from pydantic import BaseModel
from typing import Any, Literal

class SearchParams(BaseModel):
    """Search parameters for memory retrieval operations.

    This model represents the parameters used for searching memories,
    including query, version, filters, and pagination options.

    Attributes:
        query (str): Search query string.
        version (str): API version to use.
        top_k (int | None): Maximum number of results to return.
        threshold (float | None): Minimum similarity threshold for results.
        filters (dict[str, Any]): Filter conditions for the search.
        rerank (bool): Whether to apply re-ranking to search results.
    """
    query: str
    version: str
    top_k: int | None
    threshold: float | None
    filters: dict[str, Any]
    rerank: bool
    model_config: Incomplete

class GetMemoryParams(BaseModel):
    """Get memory parameters for memory retrieval operations.

    This model represents the parameters used for retrieving memories,
    including version, pagination options, and filter conditions.

    Attributes:
        page (int | None): Page number for pagination.
        page_size (int | None): Number of items per page.
        filters (dict[str, Any]): Filter conditions for the search.
        version (str): API version to use.
    """
    page: int | None
    page_size: int | None
    filters: dict[str, Any]
    version: str
    model_config: Incomplete

class Mem0Message(BaseModel):
    '''Pydantic model for Mem0 message format.

    This model ensures type safety and validation for Mem0 API message format.
    It represents the structure expected by the Mem0 API for message data.

    Attributes:
        role (Literal["user", "assistant", "system"]): The role of the message sender.
        content (str): The content of the message.
    '''
    role: Literal['user', 'assistant', 'system']
    content: str
    model_config: Incomplete

class Mem0AddParams(BaseModel):
    """Parameters for Mem0 add memory operations.

    This model represents the parameters used for adding memories to Mem0,
    including messages, version, output format, and operational flags.

    Attributes:
        messages (list[dict[str, Any]]): List of message dictionaries to add.
        version (ApiVersion): API version to use for the operation. Defaults to ApiVersion.V2.
        output_format (OutputFormat): Output format for the API response. Defaults to OutputFormat.V1_1.
        infer (bool): Whether to perform inference on the messages. Defaults to True.
        custom_instructions (str | None): Custom instructions for the operation. Defaults to None.
        async_mode (bool): Whether to perform the operation in async mode. Defaults to False.
    """
    messages: list[dict[str, Any]]
    version: ApiVersion
    output_format: OutputFormat
    infer: bool
    custom_instructions: str | None
    async_mode: bool
    model_config: Incomplete
