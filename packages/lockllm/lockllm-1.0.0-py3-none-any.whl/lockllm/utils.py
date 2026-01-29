"""Utility functions for LockLLM SDK."""

import hashlib
import random
import string
import time
from typing import Dict, Optional, cast

from .types.providers import PROVIDER_BASE_URLS, ProviderName


def generate_request_id() -> str:
    """Generate a unique request ID.

    Returns:
        A random 16-character hexadecimal string
    """
    random_bytes = "".join(random.choices(string.ascii_lowercase + string.digits, k=16))
    return hashlib.md5(f"{time.time()}{random_bytes}".encode()).hexdigest()[:16]


def calculate_backoff(
    attempt: int, base_delay: int = 1000, max_delay: int = 30000
) -> int:
    """Calculate exponential backoff delay in milliseconds.

    Args:
        attempt: The retry attempt number (0-indexed)
        base_delay: Base delay in milliseconds (default: 1000)
        max_delay: Maximum delay in milliseconds (default: 30000)

    Returns:
        Delay in milliseconds with exponential backoff
    """
    delay = min(base_delay * (2**attempt), max_delay)
    # Add jitter to avoid thundering herd
    jitter = random.uniform(0, 0.1 * delay)
    return int(delay + jitter)


def parse_retry_after(retry_after: Optional[str]) -> Optional[int]:
    """Parse Retry-After header to milliseconds.

    Args:
        retry_after: Value from Retry-After header (seconds or HTTP date)

    Returns:
        Delay in milliseconds, or None if parsing fails
    """
    if not retry_after:
        return None

    try:
        # Try as seconds
        return int(retry_after) * 1000
    except ValueError:
        # Try as HTTP date
        try:
            from datetime import datetime, timezone
            from email.utils import parsedate_to_datetime

            date = parsedate_to_datetime(retry_after)
            now = datetime.now(timezone.utc)
            delta = (date - now).total_seconds()
            return max(0, int(delta * 1000))
        except Exception:
            return None


def get_proxy_url(provider: ProviderName) -> str:
    """Get the proxy URL for a specific provider.

    Args:
        provider: Name of the provider

    Returns:
        Full proxy URL for the provider

    Example:
        >>> get_proxy_url('openai')
        'https://api.lockllm.com/v1/proxy/openai'
    """
    return PROVIDER_BASE_URLS[provider]


def get_all_proxy_urls() -> Dict[ProviderName, str]:
    """Get proxy URLs for all supported providers.

    Returns:
        Dictionary mapping provider names to proxy URLs

    Example:
        >>> urls = get_all_proxy_urls()
        >>> urls['openai']
        'https://api.lockllm.com/v1/proxy/openai'
    """
    return cast(Dict[ProviderName, str], PROVIDER_BASE_URLS.copy())
