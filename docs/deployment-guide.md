# AI Compliance Platform - Deployment Guide

## Overview

This guide covers deploying the AI Compliance Platform in various environments, from local development to production VPC deployments.

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- OpenAI API key (or Azure OpenAI credentials)
- PostgreSQL 15+ (included in Docker Compose)
- Node.js 20+ (for dashboard development)

## Quick Start (Development)

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd ai-compliance

# Copy environment file
cp env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Configure Environment Variables

Required variables in `.env`:

```bash
# Required: AI Provider
OPENAI_API_KEY=sk-your-api-key-here

# Required: Security
JWT_SECRET=your-secure-random-string-here
SECRET_KEY=another-secure-random-string

# Optional: Database (defaults work for Docker)
POSTGRES_PASSWORD=your-secure-db-password
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Verify Installation

```bash
# Check gateway health
curl http://localhost:8000/health

# Check audit service health
curl http://localhost:8001/health

# Access dashboard
open http://localhost:3000
```

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Gateway | 8000 | AI proxy endpoint |
| Audit | 8001 | Audit API & auth |
| Dashboard | 3000 | Web UI |
| PostgreSQL | 5432 | Database |

## Production Deployment

### Architecture Recommendations

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │   (TLS Term)    │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   Gateway     │ │    Audit      │ │   Dashboard   │
    │   (x2-3)      │ │    (x2-3)     │ │    (x2)       │
    └───────┬───────┘ └───────┬───────┘ └───────────────┘
            │                 │
            │                 ▼
            │         ┌───────────────┐
            │         │  PostgreSQL   │
            └────────▶│  (Managed)    │
                      └───────────────┘
```

### 1. Use Managed Database

Replace the Docker PostgreSQL with a managed service:

- AWS RDS for PostgreSQL
- Google Cloud SQL
- Azure Database for PostgreSQL

Update `DATABASE_URL` in your configuration.

### 2. Configure TLS

Place services behind a load balancer with TLS termination:

```nginx
# Example nginx configuration
server {
    listen 443 ssl;
    server_name compliance.yourcompany.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /api/ {
        proxy_pass http://audit:8001;
    }
    
    location /v1/ {
        proxy_pass http://gateway:8000;
    }
    
    location / {
        proxy_pass http://dashboard:3000;
    }
}
```

### 3. Configure Secrets Management

Use a secrets manager instead of environment files:

- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

### 4. Enable Monitoring

Add observability stack:

```yaml
# docker-compose.prod.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 5. Backup Strategy

Configure PostgreSQL backups:

```bash
# Daily backup script
#!/bin/bash
pg_dump $DATABASE_URL | gzip > /backups/ai_compliance_$(date +%Y%m%d).sql.gz

# Retain 30 days
find /backups -name "*.sql.gz" -mtime +30 -delete
```

## Kubernetes Deployment

### Helm Chart (Basic)

```yaml
# values.yaml
gateway:
  replicas: 2
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

audit:
  replicas: 2
  resources:
    requests:
      cpu: 100m
      memory: 256Mi

dashboard:
  replicas: 2

postgresql:
  enabled: false  # Use managed database
  externalHost: your-rds-endpoint.amazonaws.com
```

## Demo Mode

For pilots and demos, seed sample data:

```bash
# Seed 30 days of demo data
docker-compose exec audit python /app/demo/seed_data.py --days 30 --requests 100

# Or run locally
cd demo
pip install -r requirements.txt
python seed_data.py --days 30
```

Demo login credentials:
- Admin: `admin@demo.com` (any password)
- Analyst: `analyst@demo.com` (any password)
- Viewer: `viewer@demo.com` (any password)

## Updating

### Rolling Update

```bash
# Pull latest images
docker-compose pull

# Restart services one at a time
docker-compose up -d --no-deps gateway
docker-compose up -d --no-deps audit
docker-compose up -d --no-deps dashboard
```

### Database Migrations

```bash
# Run migrations
docker-compose exec audit alembic upgrade head
```

## Troubleshooting

### Common Issues

**Gateway can't connect to audit service:**
```bash
# Check network
docker network inspect ai-compliance_compliance-network

# Check audit service logs
docker-compose logs audit
```

**Database connection errors:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U compliance_user -d ai_compliance
```

**Dashboard shows no data:**
```bash
# Seed demo data
docker-compose exec audit python /app/demo/seed_data.py

# Check API connectivity
curl http://localhost:8001/api/v1/logs
```

### Health Checks

```bash
# All services health
curl http://localhost:8000/health  # Gateway
curl http://localhost:8001/health  # Audit
curl http://localhost:3000         # Dashboard
```

## Support

For issues and questions:
1. Check logs: `docker-compose logs -f`
2. Review documentation in `/docs`
3. Contact support team


