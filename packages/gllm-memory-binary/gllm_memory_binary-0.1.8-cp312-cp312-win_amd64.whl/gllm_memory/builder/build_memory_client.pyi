from gllm_memory.clients.mem0.mem0_client import Mem0Client as Mem0Client
from gllm_memory.clients.memory_client import BaseMemoryClient as BaseMemoryClient
from gllm_memory.enums import MemoryProviderType as MemoryProviderType

def build_memory_client(provider: str, **kwargs) -> BaseMemoryClient:
    """Create a memory client for the specified provider.

    Args:
        provider (str): The name of the memory provider.
        **kwargs: Additional keyword arguments passed to the client constructor.

    Returns:
        BaseMemoryClient: The created memory client instance.

    Raises:
        ValueError: If the provider is not supported.
    """
def build_from_env(api_key: str | None = None, instruction: str | None = None, host: str | None = None) -> BaseMemoryClient:
    """Create a memory client from environment variables or provided parameters.

    Reads configuration from environment variables to create a memory client.
    Supports MEM0_API_KEY for authentication. If api_key is provided, it takes precedence
    over the environment variable.

    Args:
        api_key (str | None, optional): API key for authentication. If None, will be read
            from MEM0_API_KEY environment variable. Defaults to None.
        instruction (str | None, optional): Custom instructions for memory handling.
            Defaults to None.
        host (str | None, optional): Host for the memory client.
            Defaults to None.

    Returns:
        BaseMemoryClient: The created memory client instance.

    Raises:
        RuntimeError: If API key is not provided and MEM0_API_KEY environment variable is missing.
        ValueError: If the provider specified in environment is not supported.
    """
