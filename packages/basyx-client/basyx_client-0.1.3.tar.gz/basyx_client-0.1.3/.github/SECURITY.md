# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **Do NOT open a public GitHub issue** for security vulnerabilities
2. Email the maintainers directly at the email associated with this repository
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Assessment**: We will assess the vulnerability and determine its severity
- **Fix Timeline**: Critical vulnerabilities will be addressed as quickly as possible
- **Disclosure**: We will coordinate with you on public disclosure timing

## Security Considerations

### Authentication Credentials

basyx-client supports various authentication methods. When using these:

- **Never commit credentials** to version control
- Use environment variables or secure credential stores
- Rotate credentials regularly
- Use the principle of least privilege

```python
# Good: Use environment variables
import os
from basyx_client import AASClient
from basyx_client.auth import BearerAuth

client = AASClient(
    os.environ["AAS_SERVER_URL"],
    auth=BearerAuth(os.environ["AAS_TOKEN"])
)
```

### mTLS Certificates

When using mutual TLS:

- Store private keys securely with restricted file permissions
- Use separate certificates for different environments
- Monitor certificate expiration

### Network Security

- Always use HTTPS in production environments
- Verify server certificates (default behavior)
- Only disable certificate verification in controlled test environments

## Dependencies

We monitor our dependencies for known vulnerabilities using GitHub's Dependabot. Security updates to dependencies are prioritized.
