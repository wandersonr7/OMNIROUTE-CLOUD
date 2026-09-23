# Architecture

## Local MVP

1. A client sends an OpenAI-compatible request.
2. FastAPI validates the request and applies a per-client in-memory rate limit.
3. The router selects mock, OpenAI-compatible, or Anthropic.
4. The adapter normalizes the provider response to the OpenAI chat-completion shape.
5. JSON logs include a request ID.

The default path is entirely local and free:

```text
Client -> FastAPI -> Router -> Mock provider
```

## Planned AWS production path

```text
Client -> Application Load Balancer -> ECS Fargate -> Provider API
                                      |-> CloudWatch Logs
                                      |-> DynamoDB metadata
                                      |-> Secrets Manager
```

Terraform currently creates only a reviewed foundation: ECR, ECS cluster, CloudWatch log group, and an encrypted DynamoDB table. A public service, load balancer, networking, Secrets Manager values, alarms, and deployment workflow must be added and cost-reviewed before deployment.

## Production gaps

- Distributed rate limiting
- Authentication and tenant isolation
- Retry/backoff and circuit breaking
- Streaming responses
- Usage metering and budgets
- Secrets Manager integration
- ECS service, VPC, ALB, autoscaling, alarms, and rollback
- DynamoDB request metadata integration
