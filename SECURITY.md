# Security policy

- Never commit API keys, AWS credentials, tokens, account IDs, or private data.
- Use `.env` only for local development; it is ignored by Git.
- Use AWS Secrets Manager for production credentials.
- Keep mock mode enabled until a paid provider is intentionally configured.
- Review Terraform plans before any apply.
- Report suspected credential exposure by revoking the credential first, then opening a private security report.
