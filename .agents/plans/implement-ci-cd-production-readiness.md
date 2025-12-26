# Module 9: CI/CD Pipeline & Production Readiness

## Overview

Establish production-ready CI/CD infrastructure with automated testing, deployment, and monitoring to ensure code quality and system reliability.

## Implementation Status: Planning

## Goals

1. **Automated Quality Gates** - CI pipeline with testing, linting, type checking
2. **Deployment Automation** - Docker build, push, and deployment workflows
3. **Production Monitoring** - Health checks, metrics, error tracking
4. **Documentation** - Production deployment guide, runbook

## Phase 1: CI/CD Pipeline

### 1.1 GitHub Actions CI Workflow

**File:** `.github/workflows/ci.yml`

**Triggers:**
- Push to `master` or `main`
- Pull requests
- Manual workflow dispatch

**Jobs:**

#### Job 1: Lint & Format Check
```yaml
lint:
  runs-on: ubuntu-latest
  steps:
    - Checkout code
    - Setup Python 3.12 with uv
    - Install dependencies
    - Run: uv run ruff check .
    - Run: uv run ruff format --check .
```

#### Job 2: Type Checking
```yaml
type-check:
  runs-on: ubuntu-latest
  steps:
    - Checkout code
    - Setup Python 3.12 with uv
    - Install dependencies
    - Run: uv run mypy app/
    - Run: uv run pyright app/
```

#### Job 3: Unit Tests
```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - Checkout code
    - Setup Python 3.12 with uv
    - Install dependencies
    - Run: uv run pytest -v --cov=app --cov-report=xml
    - Upload coverage to Codecov
```

#### Job 4: Integration Tests (with PostgreSQL)
```yaml
integration-test:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:15
      env:
        POSTGRES_PASSWORD: postgres
        POSTGRES_DB: obsidian_db
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
  steps:
    - Checkout code
    - Setup Python 3.12 with uv
    - Install dependencies
    - Run integration tests: uv run pytest -v -m integration
```

### 1.2 Docker Build & Push Workflow

**File:** `.github/workflows/docker-build.yml`

**Triggers:**
- Push to `master` with tag (e.g., `v1.0.0`)
- Manual workflow dispatch

**Jobs:**

#### Build and Push to Docker Hub
```yaml
docker:
  runs-on: ubuntu-latest
  steps:
    - Checkout code
    - Setup Docker Buildx
    - Login to Docker Hub
    - Build and push:
      - Image: username/obsidian-ai-agent:latest
      - Image: username/obsidian-ai-agent:${{ github.ref_name }}
    - Update deployment manifest
```

## Phase 2: Production Configuration

### 2.1 Environment-Specific Configs

**Files to create:**
- `.env.production.example` - Production environment template
- `.env.development` - Development defaults
- `.env.test` - Test environment config

**Production Config Additions:**
```bash
# Production Mode
ENVIRONMENT=production
LOG_LEVEL=INFO

# Production Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Monitoring
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
ENABLE_METRICS=true
METRICS_PORT=9090

# Security
API_KEY_ROTATION_DAYS=90
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### 2.2 Production Dockerfile Optimization

**Enhancements:**
- Multi-stage build for smaller image
- Non-root user for security
- Health check endpoint
- Proper signal handling

```dockerfile
FROM python:3.12-slim as builder
...

FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
USER appuser
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8123/health || exit 1
...
```

## Phase 3: Monitoring & Observability

### 3.1 Enhanced Health Checks

**File:** `app/core/health.py` (enhance existing)

**New Endpoints:**
- `/health` - Basic liveness check
- `/health/ready` - Readiness check (DB, vault access)
- `/health/detailed` - Full system status
- `/metrics` - Prometheus metrics

**Metrics to Track:**
- Request count by endpoint
- Response time percentiles
- Agent tool execution time
- Database query performance
- Error rates by type
- Vault operation latency

### 3.2 Structured Logging Enhancements

**Additions:**
- Request tracing with correlation IDs (already present)
- Performance logging (slow query detection)
- Error categorization
- Log aggregation ready (JSON format)

### 3.3 Error Tracking Integration

**File:** `app/core/sentry.py` (new)

**Features:**
- Sentry integration for error tracking
- Automatic error grouping
- Release tracking
- User context (API key hash)
- Performance monitoring

## Phase 4: Documentation

### 4.1 Production Deployment Guide

**File:** `docs/production-deployment.md`

**Sections:**
- Prerequisites
- Environment setup
- Database migrations
- Docker deployment
- Kubernetes manifests (optional)
- Monitoring setup
- Backup & restore
- Troubleshooting

### 4.2 Runbook

**File:** `docs/runbook.md`

**Common Scenarios:**
- Service won't start
- Database connection issues
- Vault access problems
- High memory usage
- Slow responses
- Agent tool failures

### 4.3 API Documentation Improvements

**Enhancements:**
- OpenAPI schema validation
- Example requests/responses
- Error code reference
- Rate limiting documentation

## Phase 5: Security Hardening

### 5.1 Security Enhancements

**Items:**
- API key hashing in logs
- Rate limiting implementation
- CORS configuration validation
- Input sanitization audit
- Dependency vulnerability scanning

### 5.2 Security GitHub Action

**File:** `.github/workflows/security.yml`

**Checks:**
- `pip-audit` for Python dependencies
- `safety` check for known vulnerabilities
- Secret scanning
- Docker image scanning (Trivy)

## Implementation Checklist

### CI/CD Pipeline
- [ ] Create `.github/workflows/ci.yml`
- [ ] Configure lint job (ruff)
- [ ] Configure type check job (mypy + pyright)
- [ ] Configure test job with coverage
- [ ] Configure integration test job with PostgreSQL
- [ ] Add coverage badge to README

### Docker & Deployment
- [ ] Create `.github/workflows/docker-build.yml`
- [ ] Optimize Dockerfile (multi-stage build)
- [ ] Add health check to Docker
- [ ] Create production docker-compose.yml
- [ ] Add non-root user to container

### Monitoring
- [ ] Enhance `/health` endpoint
- [ ] Add `/metrics` endpoint (Prometheus format)
- [ ] Implement Sentry integration
- [ ] Add performance logging
- [ ] Create monitoring dashboard config (Grafana)

### Documentation
- [ ] Write `docs/production-deployment.md`
- [ ] Write `docs/runbook.md`
- [ ] Update README with CI badges
- [ ] Add security documentation
- [ ] Create troubleshooting guide

### Security
- [ ] Implement rate limiting
- [ ] Add dependency vulnerability scanning
- [ ] Create security.yml workflow
- [ ] Audit input sanitization
- [ ] Document security best practices

## Success Criteria

- ✅ All CI checks pass automatically on PR
- ✅ Docker images build and push on tag
- ✅ Zero critical security vulnerabilities
- ✅ Test coverage > 80%
- ✅ Production deployment documented
- ✅ Monitoring dashboard shows key metrics
- ✅ Health checks return proper status

## Expected Outcomes

1. **Development Velocity** - Faster feedback on code quality
2. **Code Quality** - Automated gates prevent regressions
3. **Deployment Confidence** - One-click deployments with rollback
4. **System Visibility** - Real-time monitoring and alerts
5. **Production Reliability** - Faster incident detection and resolution

## Integration with Module 8

Module 9 builds on Module 8 (GitHub Agentic Coding) by:
- Adding quality gates to the PIV loop workflows
- Enabling automated deployments after agent commits
- Providing monitoring for agent-generated code
- Creating feedback loops for agent improvements

## Next Steps (Module 10+)

Potential future modules:
- **Module 10:** Conversation Persistence & History
- **Module 11:** Semantic Search with Embeddings
- **Module 12:** Advanced Agent Capabilities (RAG, Memory)
- **Module 13:** Multi-Vault & Team Features
