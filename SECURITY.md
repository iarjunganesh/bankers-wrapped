# Security Policy

## Supported Versions

This project is currently in active development for the Backblaze Generative Media Hackathon 2026.

| Version | Supported |
|---|---|
| 1.x (current) | ✅ |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Email: iarjunganesh@gmail.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within 48 hours.

## Security Notes

- All B2 assets are stored in a **private** bucket — access is only via time-limited presigned URLs
- No real customer financial data is stored — all demo data is fully synthetic
- API keys are loaded from environment variables only — never hardcoded
- The application does not store or log transaction data beyond the current pipeline session
