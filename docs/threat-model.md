# AI Compliance Platform - Threat Model

## Overview

This document outlines the security threats, attack vectors, and mitigations for the AI Compliance Platform. The platform handles sensitive data including AI prompts, API keys, and audit logs.

## Assets

| Asset | Description | Sensitivity |
|-------|-------------|-------------|
| AI API Keys | OpenAI/Azure credentials | Critical |
| Audit Logs | Immutable record of AI usage | High |
| Prompt Hashes | SHA-256 of prompt content | Medium |
| Application Keys | App identification keys | Medium |
| User Identifiers | User IDs from client apps | Medium |

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNTRUSTED (Internet)                         │
│                                                                 │
│  ┌──────────┐                              ┌──────────────────┐ │
│  │ Clients  │                              │  AI Providers    │ │
│  └────┬─────┘                              └────────▲─────────┘ │
└───────┼────────────────────────────────────────────┼────────────┘
        │                                            │
========│============================================│===============
        │            TRUST BOUNDARY                  │
========│============================================│===============
        │                                            │
┌───────▼────────────────────────────────────────────┼────────────┐
│                    TRUSTED (VPC/Internal)                       │
│                                                                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────┐ │
│  │   Gateway   │─────▶│    Audit    │─────▶│   PostgreSQL    │ │
│  │   Service   │      │   Service   │      │                 │ │
│  └─────────────┘      └─────────────┘      └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Threat Categories

### 1. Data in Transit

| Threat | Description | Likelihood | Impact | Mitigation |
|--------|-------------|------------|--------|------------|
| T1.1 | Man-in-the-middle on client-gateway | Medium | High | TLS termination at load balancer |
| T1.2 | Eavesdropping on gateway-provider | Low | Critical | HTTPS enforced to providers |
| T1.3 | Internal service interception | Low | Medium | Internal network isolation |

**Recommendations:**
- Deploy behind TLS-terminating load balancer
- Use VPC peering for provider connections where available
- Enable mTLS for inter-service communication (Phase 2)

### 2. API Key Security

| Threat | Description | Likelihood | Impact | Mitigation |
|--------|-------------|------------|--------|------------|
| T2.1 | API key exposure in logs | Medium | Critical | Keys never logged; environment variables |
| T2.2 | API key theft from memory | Low | Critical | Minimal key retention; no caching |
| T2.3 | API key in source control | High | Critical | .env files in .gitignore |

**Recommendations:**
- Use secrets manager (AWS Secrets Manager, HashiCorp Vault) in production
- Rotate keys regularly
- Implement key usage monitoring

### 3. Audit Log Integrity

| Threat | Description | Likelihood | Impact | Mitigation |
|--------|-------------|------------|--------|------------|
| T3.1 | Log tampering (UPDATE/DELETE) | Medium | High | Database triggers prevent modification |
| T3.2 | Log injection (malicious data) | Medium | Medium | Input validation; parameterized queries |
| T3.3 | Log deletion via DB admin | Low | High | Separate admin credentials; audit DB access |

**Recommendations:**
- Database triggers enforce append-only semantics
- All queries use parameterized statements (SQLAlchemy)
- Enable PostgreSQL audit logging (`pgaudit`)
- Consider log signing/hashing chain for tamper evidence (Phase 2)

### 4. Prompt Data Privacy

| Threat | Description | Likelihood | Impact | Mitigation |
|--------|-------------|------------|--------|------------|
| T4.1 | Raw prompt exposure | High | High | Only hash stored (Phase 1) |
| T4.2 | Prompt reconstruction | Low | Medium | SHA-256 is one-way; no rainbow tables |
| T4.3 | Metadata inference | Medium | Low | Minimal metadata captured |

**Recommendations:**
- Phase 1: Only SHA-256 hash of prompts stored
- Phase 2: Optional encrypted raw text with customer-managed keys
- Never log prompts to application logs

### 5. Authentication & Authorization

| Threat | Description | Likelihood | Impact | Mitigation |
|--------|-------------|------------|--------|------------|
| T5.1 | Unauthorized API access | High | Medium | X-App-Key header required |
| T5.2 | App key brute force | Medium | Medium | Rate limiting (Phase 2) |
| T5.3 | Cross-tenant data access | Medium | High | Org-based filtering enforced |

**Current State (Phase 1):**
- Simple X-App-Key header for app identification
- Internal network only (no external exposure recommended)

**Recommendations for Production:**
- Implement JWT-based authentication (Phase 2)
- Add rate limiting per app/org
- Enforce strict RBAC

### 6. Denial of Service

| Threat | Description | Likelihood | Impact | Mitigation |
|--------|-------------|------------|--------|------------|
| T6.1 | Request flooding | Medium | Medium | Async logging; non-blocking |
| T6.2 | Large payload attacks | Medium | Low | Request size limits |
| T6.3 | Database connection exhaustion | Low | High | Connection pooling |

**Recommendations:**
- Implement rate limiting
- Set request size limits (nginx/load balancer)
- Monitor connection pool usage

## Security Controls Summary

### Implemented (Phase 1)

| Control | Description |
|---------|-------------|
| Prompt hashing | SHA-256 hash instead of raw text |
| Immutable logs | Database triggers prevent modification |
| Input validation | Pydantic models validate all input |
| Parameterized queries | SQLAlchemy prevents SQL injection |
| Environment variables | Secrets not hardcoded |
| Internal networking | Services communicate over Docker network |

### Recommended for Production

| Control | Priority | Phase |
|---------|----------|-------|
| TLS termination | Critical | Before production |
| Secrets manager | Critical | Before production |
| Rate limiting | High | Phase 2 |
| JWT authentication | High | Phase 2 |
| mTLS (internal) | Medium | Phase 2 |
| Log signing | Medium | Phase 2 |
| Database encryption | Medium | Phase 2 |

## Incident Response

### Log Compromise
1. Immediately rotate all API keys
2. Audit database access logs
3. Notify affected organizations
4. Review application logs for unauthorized access

### API Key Exposure
1. Revoke exposed key immediately
2. Generate new key and update configuration
3. Audit logs for unauthorized usage during exposure window
4. Review access controls

## Compliance Considerations

| Requirement | Status | Notes |
|-------------|--------|-------|
| Data minimization | ✅ | Only hash stored, not raw prompts |
| Audit trail | ✅ | Immutable logs with timestamps |
| Access logging | ⚠️ | Phase 2: Log all API access |
| Encryption at rest | ⚠️ | Phase 2: Enable PostgreSQL TDE |
| Data retention | ✅ | Configurable retention policy |

## Review Schedule

This threat model should be reviewed:
- After each major release
- Following any security incident
- Quarterly at minimum
- When adding new integrations or data flows

