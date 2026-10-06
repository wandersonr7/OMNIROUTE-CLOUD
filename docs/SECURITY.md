\# OmniRoute Security Architecture



\## Current Security Model



OmniRoute is currently a development-stage project.



The local MVP includes:



\- Environment-based provider credentials

\- Per-client in-memory rate limiting

\- Request IDs

\- Structured JSON logging

\- Mock provider as the default local provider

\- Automated API testing



The current implementation should not be considered production-ready.



\## Trust Boundaries



Primary trust boundaries:



```text

Client

&#x20; |

&#x20; v

OmniRoute API

&#x20; |

&#x20; +--> Router

&#x20; |

&#x20; +--> Provider Adapter

&#x20;           |

&#x20;           +--> External LLM Provider

