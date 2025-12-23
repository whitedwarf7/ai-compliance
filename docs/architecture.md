# AI Compliance Platform - Architecture

## Overview

The AI Compliance Platform is a central control plane that monitors, logs, and enforces policies for AI usage across an organization. It consists of microservices designed for self-hosted deployment in VPC environments.

## System Architecture (Phase 2)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Applications                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  App 1   │  │  App 2   │  │  App 3   │  │  App N   │  │  Service │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │             │
        └─────────────┴──────┬──────┴─────────────┴─────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI Compliance Platform                                │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       Gateway Service (:8000)                          │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │  │
│  │  │ PII Detector│─▶│Policy Engine│─▶│ Enforcement │                   │  │
│  │  │  (Scanner)  │  │   (Rules)   │  │(Block/Mask) │                   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │  │
│  │                                           │                           │  │
│  │  • OpenAI-compatible API                  │ Alerts ──────────────────│──│──▶ Slack/Email
│  │  • Provider abstraction                   ▼                           │  │
│  │  • Prompt hashing              ┌─────────────────┐                   │  │
│  │  • Request blocking/masking    │  AI Providers   │                   │  │
│  │                                └─────────────────┘                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                             │                                                │
│                             │ HTTP (internal network)                        │
│                             ▼                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       Audit Service (:8001)                            │  │
│  │                                                                        │  │
│  │  • Log ingestion API           • Violations API                       │  │
│  │  • Search & filtering          • Violation summaries                  │  │
│  │  • CSV export                  • Trend analysis                       │  │
│  │  • Statistics                                                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                             │                                                │
│                             │ PostgreSQL protocol                            │
│                             ▼                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       PostgreSQL Database                              │  │
│  │                                                                        │  │
│  │  • Immutable audit logs (append-only, trigger-protected)              │  │
│  │  • Risk flags & violation metadata                                    │  │
│  │  • JSONB for flexible metadata                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### Gateway Service

The gateway service is the entry point for all AI requests. It provides:

**Core Features (Phase 1):**
- **OpenAI-compatible API**: Drop-in replacement for OpenAI client libraries
- **Provider abstraction**: Support for multiple AI providers (OpenAI, Azure OpenAI)
- **Request proxying**: Transparent forwarding of requests to configured provider
- **Metadata extraction**: Captures organization, application, and user context
- **Prompt hashing**: SHA-256 hash of prompts for audit without storing raw text
- **Async logging**: Fire-and-forget logging to audit service

**Compliance Features (Phase 2):**
- **PII Detection**: Regex-based scanning for 10+ PII types
- **Policy Engine**: YAML-based rules with org-specific overrides
- **Request Blocking**: Block requests with critical PII (Aadhaar, PAN, SSN, Credit Cards)
- **PII Masking**: Redact PII before forwarding to AI providers
- **Alerting**: Slack webhook and email notifications for violations

**Endpoints:**
- `POST /v1/chat/completions` - Chat completion proxy with PII detection
- `GET /v1/policy` - View current policy configuration
- `POST /v1/policy/reload` - Hot-reload policy from file
- `GET /health` - Health check

### PII Detection Engine

Detects the following PII types:

| Type | Description | Severity |
|------|-------------|----------|
| EMAIL | Email addresses | Medium |
| PHONE | Phone numbers (US/India) | Medium |
| PAN | India PAN card | Critical |
| AADHAAR | India Aadhaar (12 digits) | Critical |
| CREDIT_CARD | Visa, Mastercard, Amex, Discover | Critical |
| SSN | US Social Security Number | Critical |
| IP_ADDRESS | IPv4 addresses | Low |
| PASSPORT | Passport numbers | High |
| DATE_OF_BIRTH | Date patterns | Medium |

### Policy Engine

YAML-based policy configuration:

```yaml
version: "1.0"
name: "Default Compliance Policy"

rules:
  block_if:      # Block these PII types
    - AADHAAR
    - PAN
    - CREDIT_CARD
    - SSN
    
  mask_if:       # Mask these before forwarding
    - EMAIL
    - PHONE
    
  warn_if:       # Log warning but allow
    - IP_ADDRESS
    
  allowed_models:  # Model allowlist
    - gpt-4o
    - gpt-4-turbo
    
org_overrides:   # Per-org custom rules
  org-finance:
    block_if:
      - EMAIL
```

### Audit Service

The audit service manages the immutable audit log. It provides:

- **Log ingestion**: Receives logs from gateway service
- **Search & filtering**: Query logs by org, app, model, date, risk flags
- **CSV export**: Generate audit reports for compliance
- **Statistics**: Aggregate metrics on AI usage
- **Violations API**: Violation summaries, trends, and breakdowns

**Endpoints:**
- `POST /api/v1/logs` - Create audit log entry
- `GET /api/v1/logs` - List/filter audit logs
- `GET /api/v1/logs/{id}` - Get single log entry
- `GET /api/v1/logs/stats` - Get aggregate statistics
- `GET /api/v1/logs/export/csv` - Export logs as CSV
- `GET /api/v1/violations` - List violations
- `GET /api/v1/violations/summary` - Violation summary dashboard
- `GET /api/v1/violations/trends` - Violation trends over time
- `GET /api/v1/violations/by-type` - Breakdown by PII type
- `GET /health` - Health check

## Data Flow (Phase 2)

### Request Flow with Compliance

```
1. Client sends request to Gateway (/v1/chat/completions)
2. Gateway extracts metadata (X-App-Key, X-User-Id, X-Org-Id headers)
3. PII Scanner scans all messages for sensitive data
4. Policy Engine evaluates request against rules
5. Based on policy result:
   - BLOCK: Return 403, send alert, log violation
   - MASK: Replace PII with [TYPE_REDACTED], continue
   - WARN: Log warning, continue
   - ALLOW: Continue normally
6. Gateway forwards (possibly masked) request to AI provider
7. Gateway receives response from provider
8. Gateway captures response metadata (tokens, latency)
9. Gateway sends audit log to Audit Service (async)
10. Gateway returns response to client
```

### Enforcement Modes

| Mode | Block | Mask | Warn | Log |
|------|-------|------|------|-----|
| `enforce` | ✅ | ✅ | ✅ | ✅ |
| `warn` | ❌ | ❌ | ✅ | ✅ |
| `log_only` | ❌ | ❌ | ❌ | ✅ |

### Audit Log Schema (Updated)

```json
{
  "id": "uuid",
  "org_id": "organization identifier",
  "app_id": "application identifier",
  "user_id": "user identifier (optional)",
  "model": "gpt-4o",
  "provider": "openai",
  "prompt_hash": "sha256 hash of prompt",
  "token_count_input": 150,
  "token_count_output": 200,
  "latency_ms": 1500,
  "risk_flags": ["EMAIL", "PHONE"],
  "metadata": {
    "action": "masked",
    "violations": ["EMAIL", "PHONE"],
    "client_ip": "10.0.0.1"
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Deployment

### Docker Compose (Development/Single-node)

```bash
docker-compose up -d
```

Services:
- `postgres`: PostgreSQL 15 database
- `gateway`: Gateway service on port 8000
- `audit`: Audit service on port 8001

### Configuration

Key environment variables:

```bash
# Enforcement
ENFORCEMENT_MODE=enforce  # enforce | warn | log_only
PII_DETECTION_ENABLED=true
POLICY_FILE=/app/policies/default.yaml

# Alerts
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/xxx
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_TO=security@company.com
```

### Production Considerations

1. **Load Balancer**: Place behind nginx/HAProxy for TLS termination
2. **Database**: Use managed PostgreSQL (RDS, Cloud SQL) for HA
3. **Secrets**: Use secrets manager for API keys
4. **Monitoring**: Add Prometheus/Grafana for observability
5. **Backups**: Configure PostgreSQL WAL archiving
6. **Alerts**: Configure Slack/email for real-time violation alerts

## Security

See [Threat Model](threat-model.md) for security considerations.

## Phase Summary

### Phase 1 - Foundation ✅
- OpenAI-compatible gateway proxy
- Audit logging to PostgreSQL
- CSV export and search

### Phase 2 - Compliance Value ✅
- PII detection engine (10+ pattern types)
- Policy engine (YAML rules, org overrides)
- Request blocking and masking
- Slack/email alerts
- Violations API

### Phase 3 - Dashboard (Upcoming)
- React-based dashboard
- Role-based access control
- OAuth/SSO authentication
- Encryption at rest
