# AI Compliance Platform - Security Overview

## Executive Summary

The AI Compliance Platform is designed with security as a core principle. This document outlines the security measures, data handling practices, and compliance considerations for enterprise deployments.

## Security Architecture

### Data Flow Security

```
┌─────────────────────────────────────────────────────────────────┐
│                        SECURE PERIMETER                          │
│                                                                   │
│  ┌──────────┐    TLS 1.3    ┌──────────┐    Internal    ┌─────┐ │
│  │  Client  │──────────────▶│ Gateway  │───────────────▶│Audit│ │
│  └──────────┘               └────┬─────┘                └──┬──┘ │
│                                  │                         │     │
│                                  │ TLS 1.2+                │     │
│                                  ▼                         ▼     │
│                           ┌──────────┐              ┌──────────┐ │
│                           │ AI APIs  │              │PostgreSQL│ │
│                           └──────────┘              └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Security Features

| Feature | Implementation | Status |
|---------|---------------|--------|
| Transport Encryption | TLS 1.2+ for all external connections | ✅ |
| Authentication | JWT-based with OAuth2 support | ✅ |
| Authorization | Role-based access control (RBAC) | ✅ |
| Audit Logging | Immutable, append-only logs | ✅ |
| PII Protection | Detection, blocking, and masking | ✅ |
| Secrets Management | Environment variables (Vault recommended) | ✅ |

## Authentication & Authorization

### Authentication Methods

1. **JWT Tokens**
   - Access tokens expire after 24 hours (configurable)
   - Refresh tokens expire after 7 days
   - HMAC-SHA256 signing

2. **OAuth2 Integration** (Production)
   - Google OAuth2
   - GitHub OAuth2
   - Generic OIDC providers

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| Admin | Full access: manage users, policies, view all data |
| Analyst | Read + Export: view logs/violations, export reports |
| Viewer | Read-only: view logs and violations |

### Permission Matrix

| Action | Admin | Analyst | Viewer |
|--------|-------|---------|--------|
| View audit logs | ✅ | ✅ | ✅ |
| Export logs (CSV) | ✅ | ✅ | ❌ |
| View violations | ✅ | ✅ | ✅ |
| Export reports (PDF) | ✅ | ✅ | ❌ |
| Manage policies | ✅ | ❌ | ❌ |
| Manage users | ✅ | ❌ | ❌ |
| View settings | ✅ | ✅ | ✅ |
| Modify settings | ✅ | ❌ | ❌ |

## Data Protection

### PII Handling

**Detection:**
- 10+ PII pattern types detected via regex
- Patterns include: Email, Phone, SSN, Credit Card, Aadhaar, PAN, etc.
- Severity levels: Critical, High, Medium, Low

**Protection Actions:**
1. **Block**: Prevent request from reaching AI provider
2. **Mask**: Replace PII with `[TYPE_REDACTED]` placeholder
3. **Warn**: Log warning but allow request

**Storage:**
- Prompts are NOT stored in plaintext
- Only SHA-256 hash of prompts is logged
- PII types detected are logged (not the actual values)

### Database Security

**Immutability:**
```sql
-- Triggers prevent modification of audit logs
CREATE TRIGGER prevent_audit_log_update
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_log_modification();

CREATE TRIGGER prevent_audit_log_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_log_modification();
```

**Encryption at Rest:**
- Enable PostgreSQL TDE (Transparent Data Encryption)
- Use encrypted storage volumes

**Encryption in Transit:**
- PostgreSQL SSL connections
- Internal service communication over private network

### API Key Security

- API keys stored as SHA-256 hashes
- Keys never logged or displayed after creation
- Recommend rotation every 90 days

## Network Security

### Recommended Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         VPC / Private Network                    │
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Public    │    │   Private   │    │      Database       │  │
│  │   Subnet    │    │   Subnet    │    │       Subnet        │  │
│  │             │    │             │    │                     │  │
│  │  Dashboard  │    │  Gateway    │    │    PostgreSQL       │  │
│  │  (Web UI)   │◀──▶│  Audit Svc  │◀──▶│                     │  │
│  │             │    │             │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│        │                   │                                     │
│        │              ┌────┴────┐                                │
│        │              │   NAT   │                                │
│        │              └────┬────┘                                │
└────────┼───────────────────┼────────────────────────────────────┘
         │                   │
    ┌────▼────┐         ┌────▼────┐
    │ Users   │         │ AI APIs │
    └─────────┘         └─────────┘
```

### Firewall Rules

| Source | Destination | Port | Purpose |
|--------|-------------|------|---------|
| Internet | Dashboard | 443 | Web UI |
| Dashboard | Audit Service | 8001 | API calls |
| Dashboard | Gateway | 8000 | Policy API |
| Gateway | AI Providers | 443 | AI requests |
| Gateway | Audit Service | 8001 | Logging |
| All Services | PostgreSQL | 5432 | Database |

## Compliance Considerations

### Supported Compliance Frameworks

| Framework | Coverage |
|-----------|----------|
| SOC 2 Type II | Audit logging, access control |
| GDPR | Data minimization, right to audit |
| HIPAA | PHI detection, access logs |
| PCI DSS | Credit card detection, blocking |
| ISO 27001 | Information security controls |

### Audit Trail

All actions are logged with:
- Timestamp (UTC)
- User/Service ID
- Action type
- Resource affected
- IP address
- Request ID for correlation

### Data Retention

- Default retention: 365 days (configurable)
- Archived logs moved to separate table
- Export before deletion for compliance

## Incident Response

### Security Event Logging

Events logged include:
- Authentication failures
- Authorization denials
- Policy violations
- Configuration changes
- Export operations

### Alert Configuration

Configure alerts for:
```bash
# Slack webhook for violations
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/xxx

# Email alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_TO=security@yourcompany.com
```

## Security Checklist

### Pre-Deployment

- [ ] Change all default passwords
- [ ] Configure strong JWT_SECRET
- [ ] Enable TLS for all endpoints
- [ ] Configure network isolation
- [ ] Set up backup encryption
- [ ] Review and customize policies

### Ongoing

- [ ] Monitor audit logs daily
- [ ] Review access permissions monthly
- [ ] Rotate API keys quarterly
- [ ] Update dependencies monthly
- [ ] Conduct security review annually

## Contact

For security concerns or to report vulnerabilities:
- Security team email: security@yourcompany.com
- Response time: 24 hours for critical issues


