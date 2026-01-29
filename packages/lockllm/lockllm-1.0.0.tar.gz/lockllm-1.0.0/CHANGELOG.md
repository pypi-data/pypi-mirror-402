# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-17

### Added
- Initial release of LockLLM Python SDK
- Synchronous API with `LockLLM` class
- Asynchronous API with `AsyncLockLLM` class
- Direct scan API for manual validation
- Provider wrappers for 17 AI providers:
  - OpenAI
  - Anthropic
  - Groq
  - DeepSeek
  - Mistral AI
  - Perplexity
  - OpenRouter
  - Together AI
  - xAI (Grok)
  - Fireworks AI
  - Anyscale
  - Hugging Face
  - Google Gemini
  - Cohere
  - Azure OpenAI
  - AWS Bedrock
  - Google Vertex AI
- Both sync and async wrappers for all providers
- Comprehensive error handling with 7 custom exceptions
- Automatic retry with exponential backoff
- Rate limit handling with Retry-After support
- Full type hints with mypy support
- Context manager support for resource cleanup
- Configurable sensitivity levels (low/medium/high)
- Request ID tracking for debugging
- Usage statistics and debug information
- Comprehensive documentation and examples

### Features
- Prompt injection detection
- Jailbreak prevention
- System prompt extraction defense
- Instruction override detection
- Agent & tool abuse protection
- RAG & document injection scanning
- Indirect injection detection
- Evasion & obfuscation detection

[1.0.0]: https://github.com/lockllm/lockllm-pip/releases/tag/v1.0.0
