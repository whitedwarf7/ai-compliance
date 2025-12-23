# AI Compliance Platform

A central control plane for AI usage compliance that:

- **Detects AI usage** across the organization
- **Logs prompts, responses, and models** with audit trails
- **Flags sensitive data** (PII, financial, health)
- **Enforces company AI policies**
- **Produces audit-ready reports**

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Client Apps    │────▶│  Gateway Service │────▶│  AI Providers   │
│                 │     │  (FastAPI:8000) │     │  (OpenAI/Azure) │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Audit Service  │────▶│   PostgreSQL    │
                        │  (FastAPI:8001) │     │  (Audit Logs)   │
                        └─────────────────┘     └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API Key (or Azure OpenAI credentials)

### Setup

1. Clone the repository and navigate to the project directory

2. Copy the environment file and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Start all services:
   ```bash
   docker-compose up -d
   ```

4. Verify services are running:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   ```

### Usage

Replace your OpenAI API calls with the gateway endpoint:

```python
# Before
from openai import OpenAI
client = OpenAI()

# After
from openai import OpenAI
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-app-key"  # Your registered app key
)
```

Add the `X-App-Key` header for application identification:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-App-Key: your-app-key" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Services

### Gateway Service (Port 8000)

OpenAI-compatible proxy that:
- Forwards requests to configured AI provider
- Captures request/response metadata
- Logs to audit service asynchronously

### Audit Service (Port 8001)

Audit log management:
- `POST /api/v1/logs` - Ingest audit logs
- `GET /api/v1/logs` - Search and filter logs
- `GET /api/v1/logs/export/csv` - Export logs as CSV

## Configuration

See `.env.example` for all configuration options.

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | AI provider (openai/azure) | openai |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `DEFAULT_MODEL` | Default model to use | gpt-4o |
| `LOG_RETENTION_DAYS` | Days to retain logs | 365 |

## Documentation

- [Architecture](docs/architecture.md)
- [Threat Model](docs/threat-model.md)

## License

Proprietary - All Rights Reserved

