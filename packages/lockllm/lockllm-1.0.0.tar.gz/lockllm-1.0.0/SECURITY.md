# Security Policy

## Reporting Security Vulnerabilities

LockLLM takes security seriously. We appreciate your efforts to responsibly disclose your findings and will make every effort to acknowledge your contributions.

### How to Report a Vulnerability

**DO NOT** report security vulnerabilities through public GitHub issues.

Instead, please report security vulnerabilities by emailing:

**support@lockllm.com**

### What to Include in Your Report

Please include the following information to help us better understand and address the issue:

- **Type of vulnerability** (e.g., injection, authentication bypass, data exposure)
- **Full paths of source file(s)** related to the vulnerability
- **Location of the affected source code** (tag/branch/commit or direct URL)
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact assessment** - what an attacker could achieve
- **Suggested remediation** (if you have ideas)

### Response Timeline

- **Initial Response**: Within 48 hours of report submission
- **Status Update**: Within 7 days with assessment and next steps
- **Resolution**: Depends on severity and complexity, typically 30-90 days

### What to Expect

1. **Acknowledgment** - We will confirm receipt of your vulnerability report
2. **Assessment** - We will evaluate the vulnerability and its impact
3. **Remediation** - We will develop and test a fix
4. **Disclosure** - We will coordinate the public disclosure with you
5. **Credit** - We will acknowledge your contribution (unless you prefer to remain anonymous)

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Best Practices for Users

### API Key Security

**LockLLM API Keys**
- Never commit API keys to version control
- Use environment variables for storing keys
- Rotate keys regularly through the dashboard
- Revoke compromised keys immediately at https://www.lockllm.com/dashboard

**Provider API Keys**
- Only add provider keys through the LockLLM dashboard
- Never include provider keys in your application code
- Keys are encrypted at rest with AES-256
- Monitor key usage through the dashboard

### Rate Limiting

- Implement rate limiting in your application
- Use the SDK's built-in retry logic for transient failures
- Monitor `RateLimitError` exceptions and adjust as needed
- Contact support@lockllm.com for rate limit increases

### Error Handling

- Always handle `PromptInjectionError` gracefully
- Log security incidents without exposing sensitive data
- Use request IDs for incident investigation
- Implement monitoring for security events

**Secure Error Handling Example:**
```python
from lockllm import create_openai, PromptInjectionError

openai = create_openai(api_key=os.getenv("LOCKLLM_API_KEY"))

try:
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_input}]
    )
except PromptInjectionError as error:
    # Log securely - don't expose user input in logs
    logger.warning('Security threat detected', extra={
        'request_id': error.request_id,
        'confidence': error.scan_result.injection,
        'timestamp': datetime.now()
    })

    # Return user-friendly error
    return {"error": "Invalid input detected. Please try again."}, 400
```

### Input Validation

- Always scan user input before passing to LLMs
- Use appropriate sensitivity levels for your use case
- Implement additional validation for high-risk applications
- Consider scanning retrieved documents and external content

### Secure Configuration

```python
# Good - Use environment variables
client = LockLLM(
    api_key=os.getenv("LOCKLLM_API_KEY"),
    timeout=30.0,
    max_retries=3
)

# Bad - Hardcoded keys
client = LockLLM(
    api_key='llm_abc123...'  # Never do this!
)
```

### Network Security

- Always use HTTPS in production
- Implement request timeout protection
- Use the SDK's built-in retry logic
- Monitor network errors and patterns

### Monitoring and Logging

**What to Log:**
- Security incidents (blocked requests)
- Authentication failures
- Rate limit hits
- Request IDs for debugging

**What NOT to Log:**
- API keys
- Full user prompts (only metadata)
- Provider API keys
- Personal information

## Security Features

### Data Privacy

- **Zero Storage**: Prompts are never stored, only scanned in-memory
- **Metadata Only**: Only non-sensitive metadata is logged
- **Encryption**: All data encrypted in transit (TLS 1.3)
- **Compliance**: GDPR and SOC 2 compliant architecture

### Authentication

- Bearer token authentication for all API requests
- API keys encrypted with AES-256 at rest
- Keys never exposed in responses or logs
- Easy rotation through dashboard

### Threat Detection

- **Prompt Injection**: ML-based detection of injection attacks
- **Jailbreak Detection**: Identifies policy bypass attempts
- **System Prompt Extraction**: Prevents secret leakage
- **Tool Abuse**: Detects agent hijacking
- **RAG Injection**: Scans for poisoned context
- **Obfuscation**: Catches encoded attacks

## Known Limitations

### Network Security
- SDK relies on TLS for transport security
- Custom base_url configurations are not validated
- Users are responsible for network-level security

### Rate Limiting
- Free tier: 1,000 requests per minute
- Aggressive retry logic may compound rate limit issues
- Monitor rate limit errors in production

### Input Size
- Maximum input size: 100,000 characters
- Larger inputs may be chunked (affects latency)
- Performance degrades with very large inputs

## Disclosure Policy

### Coordinated Disclosure

We follow responsible disclosure principles:

1. **Private Notification** - We will notify you before public disclosure
2. **Coordination** - We will work with you on disclosure timing
3. **Credit** - We will credit you in release notes (unless anonymous)
4. **Timeline** - Typically 90 days from report to public disclosure

### Public Disclosure

After a fix is released:

- **Security Advisory** - Published on GitHub
- **CVE Assignment** - For critical vulnerabilities
- **Release Notes** - Included in CHANGELOG.md
- **Blog Post** - For significant vulnerabilities

## Security Updates

### How to Stay Informed

- Watch the GitHub repository for security advisories
- Subscribe to security notifications at https://www.lockllm.com/security
- Follow @lockllm on Twitter for announcements
- Monitor CHANGELOG.md for security fixes

### Updating the SDK

```bash
# Check current version
pip show lockllm

# Update to latest version
pip install --upgrade lockllm

# Or install specific version
pip install lockllm==1.1.0
```

## Bug Bounty Program

We currently do not have a formal bug bounty program. However, we deeply appreciate security researchers and will:

- Acknowledge your contribution publicly (unless you prefer anonymity)
- Provide swag and credits for significant findings
- Consider financial compensation for critical vulnerabilities on a case-by-case basis

## Security Audits

LockLLM undergoes regular security assessments:

- **Code Reviews**: All code changes reviewed for security implications
- **Dependency Audits**: Automated scanning of dependencies
- **Penetration Testing**: Annual third-party security assessments
- **Compliance Reviews**: Regular GDPR and SOC 2 compliance checks

## Questions?

For general security questions or concerns:

- **General Support**: support@lockllm.com
- **Documentation**: https://www.lockllm.com/docs

---

**Last Updated**: January 2026

Thank you for helping keep LockLLM and our users secure!
