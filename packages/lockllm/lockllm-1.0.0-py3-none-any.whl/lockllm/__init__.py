"""LockLLM Python SDK - Enterprise-grade AI security for LLM apps.

LockLLM provides real-time prompt injection and jailbreak detection
across 17+ LLM providers with both synchronous and asynchronous APIs.

Basic usage:
    >>> from lockllm import LockLLM
    >>> lockllm = LockLLM(api_key="...")
    >>> result = lockllm.scan(input="Ignore previous instructions")
    >>> if not result.safe:
    ...     print(f"Malicious prompt detected: {result.injection}%")

Async usage:
    >>> from lockllm import AsyncLockLLM
    >>> async def main():
    ...     lockllm = AsyncLockLLM(api_key="...")
    ...     result = await lockllm.scan(
    ...         input="Ignore previous instructions"
    ...     )
    ...     if not result.safe:
    ...         print(f"Malicious prompt detected: {result.injection}%")

Provider wrappers:
    >>> from lockllm import create_openai
    >>> openai = create_openai(api_key="...")
    >>> response = openai.chat.completions.create(
    ...     model="gpt-4",
    ...     messages=[{"role": "user", "content": "Hello!"}]
    ... )
"""

__version__ = "1.0.0"

# Main clients
from .async_client import AsyncLockLLM
from .client import LockLLM

# Errors
from .errors import (
    AuthenticationError,
    ConfigurationError,
    LockLLMError,
    NetworkError,
    PromptInjectionError,
    RateLimitError,
    UpstreamError,
)

# Types
from .types.common import LockLLMConfig, RequestOptions
from .types.providers import PROVIDER_BASE_URLS, ProviderName
from .types.scan import Debug, ScanRequest, ScanResponse, ScanResult, Sensitivity, Usage

# Utilities
from .utils import get_all_proxy_urls, get_proxy_url

# Provider wrappers
from .wrappers import (
    create_anthropic,
    create_anyscale,
    create_async_anthropic,
    create_async_anyscale,
    create_async_azure,
    create_async_bedrock,
    create_async_cohere,
    create_async_deepseek,
    create_async_fireworks,
    create_async_gemini,
    create_async_groq,
    create_async_huggingface,
    create_async_mistral,
    create_async_openai,
    create_async_openrouter,
    create_async_perplexity,
    create_async_together,
    create_async_vertex_ai,
    create_async_xai,
    create_azure,
    create_bedrock,
    create_cohere,
    create_deepseek,
    create_fireworks,
    create_gemini,
    create_groq,
    create_huggingface,
    create_mistral,
    create_openai,
    create_openrouter,
    create_perplexity,
    create_together,
    create_vertex_ai,
    create_xai,
)

__all__ = [
    # Version
    "__version__",
    # Main clients
    "LockLLM",
    "AsyncLockLLM",
    # Errors
    "LockLLMError",
    "AuthenticationError",
    "RateLimitError",
    "PromptInjectionError",
    "UpstreamError",
    "ConfigurationError",
    "NetworkError",
    # Types
    "LockLLMConfig",
    "RequestOptions",
    "ProviderName",
    "PROVIDER_BASE_URLS",
    "ScanRequest",
    "ScanResponse",
    "ScanResult",
    "Usage",
    "Debug",
    "Sensitivity",
    # Utilities
    "get_proxy_url",
    "get_all_proxy_urls",
    # Provider wrappers - OpenAI
    "create_openai",
    "create_async_openai",
    # Anthropic
    "create_anthropic",
    "create_async_anthropic",
    # Groq
    "create_groq",
    "create_async_groq",
    # DeepSeek
    "create_deepseek",
    "create_async_deepseek",
    # Mistral
    "create_mistral",
    "create_async_mistral",
    # Perplexity
    "create_perplexity",
    "create_async_perplexity",
    # OpenRouter
    "create_openrouter",
    "create_async_openrouter",
    # Together
    "create_together",
    "create_async_together",
    # xAI
    "create_xai",
    "create_async_xai",
    # Fireworks
    "create_fireworks",
    "create_async_fireworks",
    # Anyscale
    "create_anyscale",
    "create_async_anyscale",
    # Hugging Face
    "create_huggingface",
    "create_async_huggingface",
    # Gemini
    "create_gemini",
    "create_async_gemini",
    # Cohere
    "create_cohere",
    "create_async_cohere",
    # Azure
    "create_azure",
    "create_async_azure",
    # Bedrock
    "create_bedrock",
    "create_async_bedrock",
    # Vertex AI
    "create_vertex_ai",
    "create_async_vertex_ai",
]
