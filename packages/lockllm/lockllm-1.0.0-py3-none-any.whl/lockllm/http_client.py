"""Synchronous HTTP client with retry logic."""

import time
from typing import Any, Dict, Optional, Tuple

import requests

from .errors import LockLLMError, NetworkError, RateLimitError, parse_error
from .utils import calculate_backoff, generate_request_id, parse_retry_after


class HttpClient:
    """Synchronous HTTP client with automatic retry and error handling.

    This client handles:
    - Automatic retries with exponential backoff
    - Rate limit handling with Retry-After support
    - Request ID generation and tracking
    - Error parsing and exception raising
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the HTTP client.

        Args:
            base_url: Base URL for API requests
            api_key: LockLLM API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

    def post(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[Any, str]:
        """Make a POST request.

        Args:
            path: API endpoint path
            body: Request body (will be JSON-encoded)
            headers: Additional HTTP headers
            timeout: Override default timeout

        Returns:
            Tuple of (response data, request_id)

        Raises:
            LockLLMError: If the request fails
        """
        return self._request("POST", path, body, headers, timeout)

    def get(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[Any, str]:
        """Make a GET request.

        Args:
            path: API endpoint path
            headers: Additional HTTP headers
            timeout: Override default timeout

        Returns:
            Tuple of (response data, request_id)

        Raises:
            LockLLMError: If the request fails
        """
        return self._request("GET", path, None, headers, timeout)

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[Any, str]:
        """Internal request method with retry logic.

        Args:
            method: HTTP method
            path: API endpoint path
            body: Request body
            headers: Additional HTTP headers
            timeout: Request timeout

        Returns:
            Tuple of (response data, request_id)

        Raises:
            LockLLMError: If all retries are exhausted or error is
                not retryable
        """
        url = f"{self.base_url}{path}"
        request_id = generate_request_id()
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self._make_request(
                    method, url, body, headers, request_id, timeout
                )

                response_request_id = response.headers.get("X-Request-Id", request_id)

                # Success
                if response.ok:
                    return response.json(), response_request_id

                # Rate limiting with retry
                if response.status_code == 429:
                    if attempt < self.max_retries:
                        retry_after_header = response.headers.get("Retry-After")
                        retry_after = parse_retry_after(retry_after_header)
                        delay = retry_after or calculate_backoff(attempt)
                        time.sleep(delay / 1000.0)
                        continue

                    # Max retries exhausted for rate limit
                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {}

                    raise RateLimitError(
                        message=error_data.get("error", {}).get(
                            "message", "Rate limit exceeded"
                        ),
                        retry_after=parse_retry_after(
                            response.headers.get("Retry-After")
                        ),
                        request_id=response_request_id,
                    )

                # Other HTTP errors
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {
                        "error": {
                            "message": (
                                f"HTTP {response.status_code}: "
                                f"{response.text[:100]}"
                            )
                        }
                    }

                raise parse_error(error_data, response_request_id)

            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e

                # Retry on network errors
                if attempt < self.max_retries:
                    delay = calculate_backoff(attempt)
                    time.sleep(delay / 1000.0)
                    continue

            except LockLLMError:
                # Don't retry LockLLM errors (except rate limits handled above)
                raise

        # All retries exhausted
        raise NetworkError(
            message=(
                f"Network request failed after {self.max_retries + 1} "
                f"attempts: {last_error}"
            ),
            cause=last_error,
            request_id=request_id,
        )

    def _make_request(
        self,
        method: str,
        url: str,
        body: Optional[Dict[str, Any]],
        custom_headers: Optional[Dict[str, str]],
        request_id: str,
        timeout: Optional[float],
    ) -> requests.Response:
        """Make a single HTTP request.

        Args:
            method: HTTP method
            url: Full URL
            body: Request body
            custom_headers: Additional headers
            request_id: Request ID for tracking
            timeout: Request timeout

        Returns:
            Response object
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-Request-Id": request_id,
            "User-Agent": "lockllm-pip/1.0.0",
        }

        if custom_headers:
            headers.update(custom_headers)

        return self.session.request(
            method=method,
            url=url,
            json=body,
            headers=headers,
            timeout=timeout or self.timeout,
        )

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self) -> "HttpClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
