# AI Compliance Platform - API Reference

## Overview

The AI Compliance Platform exposes two main APIs:

1. **Gateway API** (Port 8000) - OpenAI-compatible proxy for AI requests
2. **Audit API** (Port 8001) - Audit logs, violations, reports, and authentication

## Authentication

### Obtaining Tokens

```bash
POST /api/v1/auth/login
```

**Request:**
```json
{
  "email": "admin@company.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "user": {
    "id": "user-123",
    "email": "admin@company.com",
    "name": "Admin User",
    "role": "admin"
  },
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Using Tokens

Include the token in the Authorization header:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Refreshing Tokens

```bash
POST /api/v1/auth/refresh
```

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

## Gateway API (Port 8000)

### Chat Completions

OpenAI-compatible endpoint for AI requests.

```bash
POST /v1/chat/completions
```

**Headers:**
```
Content-Type: application/json
X-App-Key: your-app-key
X-Org-Id: your-org-id
X-User-Id: optional-user-id
```

**Request:**
```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response (Success):**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

**Response (Blocked):**
```json
{
  "error": {
    "type": "policy_violation",
    "code": "pii_detected",
    "message": "Request blocked: CREDIT_CARD detected in prompt",
    "violations": ["CREDIT_CARD"],
    "request_id": "abc123"
  }
}
```

### Get Current Policy

```bash
GET /v1/policy
```

**Response:**
```json
{
  "name": "Default Compliance Policy",
  "version": "1.0",
  "rules": {
    "block_if": ["AADHAAR", "PAN", "CREDIT_CARD", "SSN"],
    "mask_if": ["EMAIL", "PHONE"],
    "allowed_models": ["gpt-4o", "gpt-4-turbo"]
  }
}
```

### Reload Policy

```bash
POST /v1/policy/reload
```

**Response:**
```json
{
  "status": "success",
  "message": "Policy reloaded"
}
```

---

## Audit API (Port 8001)

### Audit Logs

#### List Logs

```bash
GET /api/v1/logs
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org_id | string | Filter by organization |
| app_id | string | Filter by application |
| model | string | Filter by AI model |
| start_date | datetime | From date (ISO 8601) |
| end_date | datetime | To date (ISO 8601) |
| has_risk_flags | boolean | Filter flagged requests |
| page | integer | Page number (default: 1) |
| limit | integer | Items per page (max: 100) |

**Response:**
```json
{
  "items": [
    {
      "id": "log-123",
      "org_id": "org-acme",
      "app_id": "customer-support",
      "user_id": "user-456",
      "model": "gpt-4o",
      "provider": "openai",
      "prompt_hash": "abc123...",
      "token_count_input": 150,
      "token_count_output": 200,
      "latency_ms": 1500,
      "risk_flags": ["EMAIL"],
      "metadata": {"action": "masked"},
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1000,
  "page": 1,
  "limit": 50,
  "pages": 20
}
```

#### Get Single Log

```bash
GET /api/v1/logs/{log_id}
```

#### Get Statistics

```bash
GET /api/v1/logs/stats
```

**Response:**
```json
{
  "total_requests": 15847,
  "total_tokens_input": 2456000,
  "total_tokens_output": 892000,
  "unique_models": 5,
  "unique_apps": 12,
  "requests_with_risk_flags": 342
}
```

#### Export CSV

```bash
GET /api/v1/logs/export/csv
```

Returns a CSV file download.

---

### Violations

#### List Violations

```bash
GET /api/v1/violations
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| org_id | string | Filter by organization |
| app_id | string | Filter by application |
| pii_type | string | Filter by PII type |
| action | string | Filter by action (blocked/masked/warned) |
| start_date | datetime | From date |
| end_date | datetime | To date |

#### Violations Summary

```bash
GET /api/v1/violations/summary
```

**Response:**
```json
{
  "total_violations": 342,
  "total_blocked": 89,
  "total_masked": 178,
  "total_warned": 75,
  "by_type": {
    "EMAIL": 145,
    "PHONE": 87,
    "CREDIT_CARD": 45
  },
  "by_action": {
    "blocked": 89,
    "masked": 178,
    "warned": 75
  },
  "top_violating_apps": [
    {"app_id": "customer-support", "violation_count": 89}
  ]
}
```

#### Violation Trends

```bash
GET /api/v1/violations/trends?days=30
```

**Response:**
```json
{
  "trends": [
    {
      "date": "2024-01-15",
      "total": 25,
      "blocked": 8,
      "masked": 12,
      "warned": 5
    }
  ]
}
```

#### Violations by Type

```bash
GET /api/v1/violations/by-type
```

---

### Reports

#### Generate Audit Report (PDF)

```bash
GET /api/v1/reports/audit
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | datetime | Report start date |
| end_date | datetime | Report end date |
| org_id | string | Filter by organization |

Returns a PDF file download.

---

### User Management

#### Get Current User

```bash
GET /api/v1/auth/me
```

#### List Users (Admin Only)

```bash
GET /api/v1/users
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Server Error |
| 502 | AI Provider Error |
| 504 | AI Provider Timeout |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| /v1/chat/completions | 100 req/min |
| /api/v1/* | 1000 req/min |
| /api/v1/reports/* | 10 req/min |

---

## SDK Integration

### Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-app-key",
    default_headers={
        "X-App-Key": "your-app-key",
        "X-Org-Id": "your-org-id",
    }
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### JavaScript/TypeScript

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:8000/v1',
  apiKey: 'your-app-key',
  defaultHeaders: {
    'X-App-Key': 'your-app-key',
    'X-Org-Id': 'your-org-id',
  },
});

const response = await client.chat.completions.create({
  model: 'gpt-4o',
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

---

## Webhooks

Configure webhooks for real-time notifications:

```bash
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/xxx
```

Webhook payload:
```json
{
  "type": "policy_violation",
  "violations": ["CREDIT_CARD"],
  "action": "blocked",
  "app_id": "customer-support",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

