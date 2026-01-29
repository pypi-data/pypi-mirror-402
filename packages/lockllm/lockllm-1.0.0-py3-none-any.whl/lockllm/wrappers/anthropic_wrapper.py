"""Anthropic provider wrappers."""

from typing import Any, Optional

from ..errors import ConfigurationError
from ..utils import get_proxy_url


def create_anthropic(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create Anthropic client with LockLLM proxy (synchronous).

    Drop-in replacement for Anthropic client initialization. All requests
    are automatically scanned by LockLLM before being forwarded to Anthropic.

    Args:
        api_key: Your LockLLM API key (not your Anthropic key)
        base_url: Custom proxy URL
            (default: https://api.lockllm.com/v1/proxy/anthropic)
        **kwargs: Additional Anthropic client options

    Returns:
        Anthropic client configured to use LockLLM proxy

    Raises:
        ConfigurationError: If Anthropic SDK is not installed

    Example:
        >>> from lockllm import create_anthropic
        >>> anthropic = create_anthropic(api_key="...")
        >>> message = anthropic.messages.create(
        ...     model="claude-3-5-sonnet-20241022",
        ...     max_tokens=1024,
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    try:
        import anthropic
    except ImportError:
        raise ConfigurationError(
            "Anthropic SDK not found. Install it with: pip install anthropic"
        )

    return anthropic.Anthropic(
        api_key=api_key, base_url=base_url or get_proxy_url("anthropic"), **kwargs
    )


def create_async_anthropic(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Anthropic client with LockLLM proxy.

    Drop-in replacement for AsyncAnthropic client initialization. All requests
    are automatically scanned by LockLLM before being forwarded to Anthropic.

    Args:
        api_key: Your LockLLM API key (not your Anthropic key)
        base_url: Custom proxy URL
            (default: https://api.lockllm.com/v1/proxy/anthropic)
        **kwargs: Additional Anthropic client options

    Returns:
        AsyncAnthropic client configured to use LockLLM proxy

    Raises:
        ConfigurationError: If Anthropic SDK is not installed

    Example:
        >>> from lockllm import create_async_anthropic
        >>> async def main():
        ...     anthropic = create_async_anthropic(api_key="...")
        ...     message = await anthropic.messages.create(
        ...         model="claude-3-5-sonnet-20241022",
        ...         max_tokens=1024,
        ...         messages=[{"role": "user", "content": "Hello!"}]
        ...     )
    """
    try:
        import anthropic
    except ImportError:
        raise ConfigurationError(
            "Anthropic SDK not found. Install it with: pip install anthropic"
        )

    return anthropic.AsyncAnthropic(
        api_key=api_key, base_url=base_url or get_proxy_url("anthropic"), **kwargs
    )
