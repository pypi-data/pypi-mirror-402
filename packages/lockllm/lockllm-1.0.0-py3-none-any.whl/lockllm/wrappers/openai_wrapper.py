"""OpenAI provider wrappers."""

from typing import Any, Optional

from ..errors import ConfigurationError
from ..utils import get_proxy_url


def create_openai(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create OpenAI client with LockLLM proxy (synchronous).

    Drop-in replacement for OpenAI client initialization. All requests
    are automatically scanned by LockLLM before being forwarded to OpenAI.

    Args:
        api_key: Your LockLLM API key (not your OpenAI key)
        base_url: Custom proxy URL
            (default: https://api.lockllm.com/v1/proxy/openai)
        **kwargs: Additional OpenAI client options

    Returns:
        OpenAI client configured to use LockLLM proxy

    Raises:
        ConfigurationError: If OpenAI SDK is not installed

    Example:
        >>> from lockllm import create_openai
        >>> openai = create_openai(api_key="...")
        >>> response = openai.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    try:
        import openai
    except ImportError:
        raise ConfigurationError(
            "OpenAI SDK not found. Install it with: pip install openai"
        )

    return openai.OpenAI(
        api_key=api_key, base_url=base_url or get_proxy_url("openai"), **kwargs
    )


def create_async_openai(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async OpenAI client with LockLLM proxy.

    Drop-in replacement for AsyncOpenAI client initialization. All requests
    are automatically scanned by LockLLM before being forwarded to OpenAI.

    Args:
        api_key: Your LockLLM API key (not your OpenAI key)
        base_url: Custom proxy URL
            (default: https://api.lockllm.com/v1/proxy/openai)
        **kwargs: Additional OpenAI client options

    Returns:
        AsyncOpenAI client configured to use LockLLM proxy

    Raises:
        ConfigurationError: If OpenAI SDK is not installed

    Example:
        >>> from lockllm import create_async_openai
        >>> async def main():
        ...     openai = create_async_openai(api_key="...")
        ...     response = await openai.chat.completions.create(
        ...         model="gpt-4",
        ...         messages=[{"role": "user", "content": "Hello!"}]
        ...     )
    """
    try:
        import openai
    except ImportError:
        raise ConfigurationError(
            "OpenAI SDK not found. Install it with: pip install openai"
        )

    return openai.AsyncOpenAI(
        api_key=api_key, base_url=base_url or get_proxy_url("openai"), **kwargs
    )
