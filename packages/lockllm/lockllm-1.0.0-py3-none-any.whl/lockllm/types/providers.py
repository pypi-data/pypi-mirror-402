"""Provider type definitions."""

from typing import Literal

# All supported provider names
ProviderName = Literal[
    "openai",
    "anthropic",
    "gemini",
    "cohere",
    "openrouter",
    "perplexity",
    "mistral",
    "groq",
    "deepseek",
    "together",
    "xai",
    "fireworks",
    "anyscale",
    "huggingface",
    "azure",
    "bedrock",
    "vertex-ai",
]

# Base proxy URLs for each provider
PROVIDER_BASE_URLS = {
    "openai": "https://api.lockllm.com/v1/proxy/openai",
    "anthropic": "https://api.lockllm.com/v1/proxy/anthropic",
    "gemini": "https://api.lockllm.com/v1/proxy/gemini",
    "cohere": "https://api.lockllm.com/v1/proxy/cohere",
    "openrouter": "https://api.lockllm.com/v1/proxy/openrouter",
    "perplexity": "https://api.lockllm.com/v1/proxy/perplexity",
    "mistral": "https://api.lockllm.com/v1/proxy/mistral",
    "groq": "https://api.lockllm.com/v1/proxy/groq",
    "deepseek": "https://api.lockllm.com/v1/proxy/deepseek",
    "together": "https://api.lockllm.com/v1/proxy/together",
    "xai": "https://api.lockllm.com/v1/proxy/xai",
    "fireworks": "https://api.lockllm.com/v1/proxy/fireworks",
    "anyscale": "https://api.lockllm.com/v1/proxy/anyscale",
    "huggingface": "https://api.lockllm.com/v1/proxy/huggingface",
    "azure": "https://api.lockllm.com/v1/proxy/azure",
    "bedrock": "https://api.lockllm.com/v1/proxy/bedrock",
    "vertex-ai": "https://api.lockllm.com/v1/proxy/vertex-ai",
}
