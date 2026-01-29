"""Scan request and response type definitions."""

from dataclasses import dataclass
from typing import Literal, Optional

# Sensitivity level type
Sensitivity = Literal["low", "medium", "high"]


@dataclass
class ScanRequest:
    """Request to scan a prompt for security threats.

    Attributes:
        input: The text prompt to scan
        sensitivity: Detection threshold level (default: "medium")
            - "low": Fewer false positives, may miss sophisticated attacks
            - "medium": Balanced detection (recommended)
            - "high": Maximum protection, may have more false positives
    """

    input: str
    sensitivity: Sensitivity = "medium"


@dataclass
class Usage:
    """Usage statistics for the scan.

    Attributes:
        requests: Number of upstream inference requests used
        input_chars: Number of characters in the input
    """

    requests: int
    input_chars: int


@dataclass
class Debug:
    """Debug information (Pro plan only).

    Attributes:
        duration_ms: Total processing time in milliseconds
        inference_ms: ML inference time in milliseconds
        mode: Processing mode used ("single" or "chunked")
    """

    duration_ms: int
    inference_ms: int
    mode: Literal["single", "chunked"]


@dataclass
class ScanResult:
    """Core scan result data.

    Attributes:
        safe: Whether the input is safe (True) or malicious (False)
        label: Binary classification (0=safe, 1=malicious)
        confidence: Confidence score (0-100)
        injection: Injection risk score (0-100, higher=more risky)
        sensitivity: Sensitivity level used for the scan
    """

    safe: bool
    label: Literal[0, 1]
    confidence: float
    injection: float
    sensitivity: Sensitivity


@dataclass
class ScanResponse(ScanResult):
    """Complete scan response from the API.

    Attributes:
        request_id: Unique request identifier for tracking
        usage: Usage statistics
        debug: Debug information (Pro plan only, optional)
    """

    request_id: str
    usage: Usage
    debug: Optional[Debug] = None
