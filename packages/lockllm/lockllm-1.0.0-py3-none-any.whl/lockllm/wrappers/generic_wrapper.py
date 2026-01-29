"""Generic provider wrappers for OpenAI-compatible providers."""

from typing import Any, Optional

from ..errors import ConfigurationError
from ..utils import get_proxy_url


def _create_openai_compatible(
    provider: str,
    api_key: str,
    base_url: Optional[str] = None,
    is_async: bool = False,
    **kwargs: Any,
) -> Any:
    """Internal helper to create OpenAI-compatible clients.

    Args:
        provider: Provider name
        api_key: LockLLM API key
        base_url: Custom proxy URL
        is_async: Whether to create async client
        **kwargs: Additional client options

    Returns:
        OpenAI or AsyncOpenAI client configured for provider

    Raises:
        ConfigurationError: If OpenAI SDK is not installed
    """
    try:
        import openai
    except ImportError:
        raise ConfigurationError(
            "OpenAI SDK not found. Install it with: pip install openai"
        )

    client_class = openai.AsyncOpenAI if is_async else openai.OpenAI
    proxy_url = base_url or get_proxy_url(provider)  # type: ignore

    return client_class(api_key=api_key, base_url=proxy_url, **kwargs)


# Groq
def create_groq(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create Groq client (OpenAI-compatible, synchronous).

    Example:
        >>> groq = create_groq(api_key="...")
        >>> response = groq.chat.completions.create(
        ...     model='llama-3.1-70b-versatile',
        ...     messages=[{'role': 'user', 'content': 'Hello!'}]
        ... )
    """
    return _create_openai_compatible("groq", api_key, base_url, False, **kwargs)


def create_async_groq(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Groq client (OpenAI-compatible)."""
    return _create_openai_compatible("groq", api_key, base_url, True, **kwargs)


# DeepSeek
def create_deepseek(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create DeepSeek client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("deepseek", api_key, base_url, False, **kwargs)


def create_async_deepseek(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async DeepSeek client (OpenAI-compatible)."""
    return _create_openai_compatible("deepseek", api_key, base_url, True, **kwargs)


# Mistral
def create_mistral(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create Mistral AI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("mistral", api_key, base_url, False, **kwargs)


def create_async_mistral(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Mistral AI client (OpenAI-compatible)."""
    return _create_openai_compatible("mistral", api_key, base_url, True, **kwargs)


# Perplexity
def create_perplexity(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create Perplexity client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("perplexity", api_key, base_url, False, **kwargs)


def create_async_perplexity(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Perplexity client (OpenAI-compatible)."""
    return _create_openai_compatible("perplexity", api_key, base_url, True, **kwargs)


# OpenRouter
def create_openrouter(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create OpenRouter client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("openrouter", api_key, base_url, False, **kwargs)


def create_async_openrouter(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async OpenRouter client (OpenAI-compatible)."""
    return _create_openai_compatible("openrouter", api_key, base_url, True, **kwargs)


# Together
def create_together(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create Together AI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("together", api_key, base_url, False, **kwargs)


def create_async_together(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Together AI client (OpenAI-compatible)."""
    return _create_openai_compatible("together", api_key, base_url, True, **kwargs)


# xAI
def create_xai(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create xAI (Grok) client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("xai", api_key, base_url, False, **kwargs)


def create_async_xai(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async xAI (Grok) client (OpenAI-compatible)."""
    return _create_openai_compatible("xai", api_key, base_url, True, **kwargs)


# Fireworks
def create_fireworks(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create Fireworks AI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("fireworks", api_key, base_url, False, **kwargs)


def create_async_fireworks(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Fireworks AI client (OpenAI-compatible)."""
    return _create_openai_compatible("fireworks", api_key, base_url, True, **kwargs)


# Anyscale
def create_anyscale(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create Anyscale client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("anyscale", api_key, base_url, False, **kwargs)


def create_async_anyscale(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Anyscale client (OpenAI-compatible)."""
    return _create_openai_compatible("anyscale", api_key, base_url, True, **kwargs)


# Hugging Face
def create_huggingface(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create Hugging Face client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("huggingface", api_key, base_url, False, **kwargs)


def create_async_huggingface(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Hugging Face client (OpenAI-compatible)."""
    return _create_openai_compatible("huggingface", api_key, base_url, True, **kwargs)


# Gemini
def create_gemini(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create Google Gemini client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("gemini", api_key, base_url, False, **kwargs)


def create_async_gemini(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Google Gemini client (OpenAI-compatible)."""
    return _create_openai_compatible("gemini", api_key, base_url, True, **kwargs)


# Cohere
def create_cohere(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create Cohere client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("cohere", api_key, base_url, False, **kwargs)


def create_async_cohere(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Cohere client (OpenAI-compatible)."""
    return _create_openai_compatible("cohere", api_key, base_url, True, **kwargs)


# Azure
def create_azure(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create Azure OpenAI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("azure", api_key, base_url, False, **kwargs)


def create_async_azure(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Azure OpenAI client (OpenAI-compatible)."""
    return _create_openai_compatible("azure", api_key, base_url, True, **kwargs)


# Bedrock
def create_bedrock(api_key: str, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """Create AWS Bedrock client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("bedrock", api_key, base_url, False, **kwargs)


def create_async_bedrock(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async AWS Bedrock client (OpenAI-compatible)."""
    return _create_openai_compatible("bedrock", api_key, base_url, True, **kwargs)


# Vertex AI
def create_vertex_ai(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create Google Vertex AI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible("vertex-ai", api_key, base_url, False, **kwargs)


def create_async_vertex_ai(
    api_key: str, base_url: Optional[str] = None, **kwargs: Any
) -> Any:
    """Create async Google Vertex AI client (OpenAI-compatible)."""
    return _create_openai_compatible("vertex-ai", api_key, base_url, True, **kwargs)
