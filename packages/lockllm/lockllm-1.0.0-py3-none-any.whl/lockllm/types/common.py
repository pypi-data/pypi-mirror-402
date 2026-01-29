"""Common type definitions."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LockLLMConfig:
    """Configuration for LockLLM client.

    Attributes:
        api_key: Your LockLLM API key from https://www.lockllm.com/dashboard
        base_url: Custom base URL (default: https://api.lockllm.com)
        timeout: Request timeout in seconds (default: 60.0)
        max_retries: Maximum number of retry attempts (default: 3)
    """

    api_key: str
    base_url: str = "https://api.lockllm.com"
    timeout: float = 60.0
    max_retries: int = 3


@dataclass
class RequestOptions:
    """Optional request configuration.

    Attributes:
        headers: Additional HTTP headers to include
        timeout: Override default timeout for this request
    """

    headers: Optional[Dict[str, str]] = None
    timeout: Optional[float] = None
