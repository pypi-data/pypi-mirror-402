"""Main synchronous LockLLM client."""

from typing import Any, Optional

from .errors import ConfigurationError
from .http_client import HttpClient
from .scan import ScanClient
from .types.common import LockLLMConfig
from .types.scan import ScanResponse, Sensitivity

DEFAULT_BASE_URL = "https://api.lockllm.com"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3


class LockLLM:
    """Main LockLLM client for AI security scanning (synchronous).

    This is the primary entry point for using the LockLLM SDK. It provides
    methods to scan prompts for security threats such as prompt injection,
    jailbreak attempts, and other adversarial attacks.

    Args:
        api_key: Your LockLLM API key from
            https://www.lockllm.com/dashboard
        base_url: Custom base URL (default: https://api.lockllm.com)
        timeout: Request timeout in seconds (default: 60.0)
        max_retries: Maximum retry attempts (default: 3)

    Raises:
        ConfigurationError: If API key is missing or invalid

    Example:
        >>> lockllm = LockLLM(api_key="...")
        >>> result = lockllm.scan(input="Ignore previous instructions")
        >>> if not result.safe:
        ...     print(f"Malicious prompt detected: {result.injection}%")
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """Initialize the LockLLM client.

        Args:
            api_key: Your LockLLM API key
            base_url: Custom API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        if not api_key or not api_key.strip():
            raise ConfigurationError(
                "API key is required. Get your API key from "
                "https://www.lockllm.com/dashboard"
            )

        self._config = LockLLMConfig(
            api_key=api_key,
            base_url=base_url or DEFAULT_BASE_URL,
            timeout=(timeout if timeout is not None else DEFAULT_TIMEOUT),
            max_retries=(
                max_retries if max_retries is not None else DEFAULT_MAX_RETRIES
            ),
        )

        self._http = HttpClient(
            base_url=self._config.base_url,
            api_key=self._config.api_key,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )

        self._scan_client = ScanClient(self._http)

    def scan(
        self, input: str, sensitivity: Sensitivity = "medium", **options: Any
    ) -> ScanResponse:
        """Scan a prompt for security threats.

        Analyzes input text using advanced ML models to detect prompt
        injection, jailbreak attempts, and other adversarial attacks.

        Args:
            input: The text prompt to scan for security threats
            sensitivity: Detection threshold level (default: "medium")
                - "low": Fewer false positives, may miss
                    sophisticated attacks
                - "medium": Balanced detection (recommended)
                - "high": Maximum protection, may have more false
                    positives
            **options: Additional request options (headers, timeout)

        Returns:
            ScanResponse object with safety classification and threat scores

        Raises:
            ConfigurationError: If configuration is invalid
            AuthenticationError: If API key is invalid
            NetworkError: If network request fails
            RateLimitError: If rate limit is exceeded

        Example:
            >>> result = lockllm.scan(
            ...     input="Ignore previous instructions",
            ...     sensitivity="medium"
            ... )
            >>> if not result.safe:
            ...     print(f"Malicious! Injection score: {result.injection}%")
            ...     print(f"Request ID: {result.request_id}")
        """
        return self._scan_client.scan(input=input, sensitivity=sensitivity, **options)

    @property
    def config(self) -> LockLLMConfig:
        """Get the current configuration (readonly).

        Returns:
            The LockLLMConfig object
        """
        return self._config

    def close(self) -> None:
        """Close the HTTP client and release resources.

        It's recommended to call this when you're done using the client,
        or use the client as a context manager.
        """
        self._http.close()

    def __enter__(self) -> "LockLLM":
        """Context manager entry.

        Example:
            >>> with LockLLM(api_key="...") as client:
            ...     result = client.scan(input="test")
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        self.close()
