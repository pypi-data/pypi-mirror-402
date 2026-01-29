"""Asynchronous scan client."""

from typing import Any, Optional

from .async_http_client import AsyncHttpClient
from .types.scan import Debug, ScanRequest, ScanResponse, Sensitivity, Usage


class AsyncScanClient:
    """Client for scanning prompts for security threats (asynchronous).

    This client provides async methods to scan text inputs for:
    - Prompt injection attacks
    - Jailbreak attempts
    - Instruction override
    - System prompt extraction
    - Tool/function abuse
    - RAG injection
    - Obfuscation techniques
    """

    def __init__(self, http: AsyncHttpClient) -> None:
        """Initialize the async scan client.

        Args:
            http: Async HTTP client for making requests
        """
        self._http = http

    async def scan(
        self, input: str, sensitivity: Sensitivity = "medium", **options: Any
    ) -> ScanResponse:
        """Scan a prompt for security threats (async).

        Analyzes input text using advanced ML models to detect prompt
        injection, jailbreak attempts, and other adversarial attacks.

        Args:
            input: The text prompt to scan for security threats
            sensitivity: Detection threshold level
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
            >>> client = AsyncScanClient(http)
            >>> result = await client.scan(
            ...     input="Ignore previous instructions",
            ...     sensitivity="medium"
            ... )
            >>> if not result.safe:
            ...     print(f"Malicious! Injection score: {result.injection}%")
        """
        request = ScanRequest(input=input, sensitivity=sensitivity)
        body = {"input": request.input, "sensitivity": request.sensitivity}

        # Extract request options
        headers = options.get("headers")
        timeout = options.get("timeout")

        data, request_id = await self._http.post(
            "/v1/scan", body=body, headers=headers, timeout=timeout
        )

        # Parse response
        return self._parse_response(data, request_id)

    def _parse_response(self, data: dict, request_id: str) -> ScanResponse:
        """Parse API response into ScanResponse.

        Args:
            data: Response data from API
            request_id: Request ID

        Returns:
            Parsed ScanResponse object
        """
        # Parse usage
        usage_data = data.get("usage", {})
        usage = Usage(
            requests=usage_data.get("requests", 0),
            input_chars=usage_data.get("input_chars", 0),
        )

        # Parse debug (optional, Pro plan only)
        debug: Optional[Debug] = None
        if "debug" in data:
            debug_data = data["debug"]
            debug = Debug(
                duration_ms=debug_data.get("duration_ms", 0),
                inference_ms=debug_data.get("inference_ms", 0),
                mode=debug_data.get("mode", "single"),
            )

        return ScanResponse(
            safe=data["safe"],
            label=data["label"],
            confidence=data["confidence"],
            injection=data["injection"],
            sensitivity=data["sensitivity"],
            request_id=data.get("request_id", request_id),
            usage=usage,
            debug=debug,
        )
