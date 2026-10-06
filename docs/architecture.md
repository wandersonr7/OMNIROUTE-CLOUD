# OmniRoute Cloud Architecture

## Overview

OmniRoute Cloud is a multi-provider AI routing gateway built with FastAPI.

It provides a single API entry point that can route chat-completion requests to multiple AI providers while adding reliability controls such as:

- configurable timeouts
- retries
- exponential backoff
- circuit breakers
- provider health tracking
- automatic failover
- structured logging
- rate limiting

The project currently supports:

- Mock provider
- OpenAI-compatible provider
- Anthropic provider

---

## Current Request Flow

```text
Client
  |
  v
FastAPI
  |
  +--> Request ID middleware
  |
  +--> In-memory rate limiter
  |
  +--> Provider routing
          |
          +--> Provider health check
          |
          +--> Circuit breaker check
          |
          +--> Primary provider
          |       |
          |       +--> Timeout
          |       +--> Retry
          |       +--> Exponential backoff
          |
          +--> Failover provider
                  |
                  +--> OpenAI
                  +--> Anthropic
                  +--> Mock