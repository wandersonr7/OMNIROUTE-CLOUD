# OmniRoute Cloud

OmniRoute Cloud is a portfolio-grade API gateway that routes OpenAI-compatible chat requests to multiple AI providers.

## Current status

This repository contains a safe local MVP. It runs in **mock mode by default**, so it does not require an API key and does not generate AWS or model-provider charges.

Implemented:

- OpenAI-compatible `POST /v1/chat/completions`
- `GET /health` health check
- Mock, OpenAI-compatible, and Anthropic provider adapters
- Provider selection through `X-OmniRoute-Provider`
- In-memory rate limiting
- Structured JSON logs
- Docker and Docker Compose
- Automated tests and GitHub Actions
- Terraform foundation for ECR, ECS, CloudWatch, and DynamoDB

Not activated:

- AWS deployment
- Paid model APIs
- Production secrets
- Public endpoint

## Run locally for free

### Docker

```bash
docker compose up --build
```

Open <http://localhost:8080/health>.

### Python

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8080
```

## Free test

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"mock-1","messages":[{"role":"user","content":"Hello OmniRoute"}]}'
```

The response comes from the local mock provider.

## Real providers

Copy `.env.example` to `.env`. Never commit the resulting `.env`.

- OpenAI-compatible: set `OPENAI_API_KEY`, optionally `OPENAI_BASE_URL`, then send `X-OmniRoute-Provider: openai`.
- Anthropic: set `ANTHROPIC_API_KEY`, then send `X-OmniRoute-Provider: anthropic`.

Real provider usage may incur charges.

## Safety

The Terraform directory is planning material only. Do not run `terraform apply` until AWS billing alerts, IAM permissions, networking, and a destruction plan are reviewed.

The former website is preserved in branch `archive/portfolio-before-omniroute`.

See [docs/architecture.md](docs/architecture.md) and [SECURITY.md](SECURITY.md).
