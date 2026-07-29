# Krama AI

**AI Claims Engine for Insurance** — Turn discharge summaries, repair estimates, and claim forms into validated, fraud-checked decisions in minutes.

🌐 **Live:** [kramaai.com](https://kramaai.com)

---

## What It Does

Krama AI automates insurance claims processing for Indian insurers and TPAs. Upload any claim document — discharge summaries, hospital bills, FIRs, repair estimates, pharmacy receipts — in any format (PDF, scan, photo, handwritten Hindi) and get a structured, validated claim decision.

### Pipeline

```
Document Upload → Ingestion → Conversion → OCR → Classification → Field Extraction → Validation → Fraud Detection → Review → Decision
```

- **Ingest** — PDF, scans, photos, XLSX, PPTX. Handles handwritten Hindi/English. Chunked streaming uploads up to 50 MB per file, 500 MB batch.
- **Convert** — PDFs rendered to images at configurable DPI. Multi-page document support (up to 500 pages). Page-level pixel safety limits.
- **Extract** — OCR + VLM (Gemini / OpenAI / Ollama / local) for field-level extraction with confidence scores.
- **Validate** — Triple validation cross-checks OCR, VLM, and structural patterns. Flags anomalies with fuzzy matching.
- **Review** — Human-in-the-loop review workflow with auto-approval thresholds and IRDAI policy checks.
- **Decide** — Fraud detection, auto-adjudication recommendations, and full audit trail.

---

## Supported Document Types

| Category | Documents |
|----------|-----------|
| **Medical** | Discharge Summary, Lab Report, Prescription, Medical Certificate |
| **Financial** | Hospital Bill, Pharmacy Receipt, Repair Estimate, Invoice |
| **Insurance** | Claim Form, Policy Document, Cashless Authorization, Surveyor Report |
| **Identity** | Aadhaar Card, PAN Card, Driving License, Voter ID |
| **Vehicle** | RC Book, FIR Copy, Accident Report |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Database** | SQLAlchemy 2.x ORM, Alembic migrations (SQLite dev / PostgreSQL prod) |
| **OCR** | PaddleOCR (pluggable provider) |
| **Vision LLM** | Gemini 2.0 Flash / GPT-4o / Ollama (configurable, with fallback chain) |
| **Security** | JWT (PyJWT), bcrypt password hashing, API key authentication, RBAC |
| **Caching** | In-memory (default) or Redis |
| **Observability** | Prometheus metrics, OpenTelemetry tracing (OTLP), structured JSON logging |
| **Reliability** | Circuit breakers, rate limiting, async job queue with retry/backoff |
| **Analytics** | Cost tracking, SLA reporting, XLSX/PDF export (openpyxl, fpdf2) |
| **Frontend** | HTML/CSS/JS (served as static files) |
| **Deployment** | Docker, Kubernetes (Helm charts), Vercel (frontend) |

---

## Project Structure

```
krama_labs/
├── index.html                    # Frontend landing page
├── assets/                       # Frontend static assets
├── favicon.svg
├── vercel.json                   # Vercel deployment config
├── Dockerfile                    # Root Dockerfile
│
└── backend/
    ├── Dockerfile                # Backend-specific Dockerfile
    ├── requirements.txt          # Core dependencies
    ├── requirements-ml.txt       # ML/OCR dependencies
    ├── alembic.ini               # Alembic migration config
    ├── alembic/                  # Database migration scripts
    │   └── versions/
    │
    ├── app/
    │   ├── main.py               # FastAPI application factory
    │   │
    │   ├── core/
    │   │   ├── config.py         # Centralized configuration (env-driven)
    │   │   └── exceptions.py     # Custom exception hierarchy & handlers
    │   │
    │   ├── api/
    │   │   ├── router.py         # Central API router registry
    │   │   └── routes/
    │   │       ├── health.py     # Health check & readiness
    │   │       ├── document.py   # Document upload & processing
    │   │       ├── chat.py       # AI chat on processed results
    │   │       ├── demo.py       # Demo endpoints
    │   │       ├── auth.py       # JWT login/logout/refresh
    │   │       ├── apikeys.py    # API key management
    │   │       ├── analytics.py  # Analytics & reporting
    │   │       ├── admin.py      # Admin operations
    │   │       ├── observability.py  # /metrics & observability status
    │   │       └── v1/           # Versioned production routes
    │   │           ├── organizations.py
    │   │           ├── claims.py
    │   │           ├── documents.py
    │   │           ├── jobs.py
    │   │           ├── jobs_async.py  # Async job execution
    │   │           ├── pages.py
    │   │           ├── providers.py
    │   │           └── review.py
    │   │
    │   ├── services/             # Business logic layer
    │   │   ├── pipeline.py       # End-to-end document pipeline
    │   │   ├── ingestion_service.py
    │   │   ├── conversion_service.py
    │   │   ├── ocr_service.py
    │   │   ├── classification_service.py
    │   │   ├── extraction_service.py
    │   │   ├── validation_service.py
    │   │   ├── review_service.py
    │   │   ├── claim_service.py
    │   │   ├── workflow_orchestrator.py
    │   │   ├── final_document_resolver.py
    │   │   ├── job_service.py
    │   │   ├── rate_limiter.py
    │   │   ├── redis_cache.py
    │   │   └── distributed_lock.py
    │   │
    │   ├── db/
    │   │   ├── session.py        # SQLAlchemy session factory
    │   │   ├── base.py           # Declarative base
    │   │   └── models/           # ORM models (orgs, claims, docs, jobs, users…)
    │   │
    │   ├── repositories/         # Data access layer (repository pattern)
    │   ├── schemas/              # Pydantic request/response schemas
    │   ├── models/               # Domain model types
    │   │
    │   ├── engines/              # Low-level processing engines
    │   │   ├── ocr_engine.py
    │   │   ├── vlm_engine.py
    │   │   ├── classifier.py
    │   │   ├── ocr_extractor.py
    │   │   ├── chunker.py
    │   │   ├── converter.py
    │   │   ├── grounding.py
    │   │   ├── validator.py
    │   │   └── llm_provider.py
    │   │
    │   ├── ocr/                  # OCR provider abstraction
    │   ├── classification/       # Document type classification
    │   ├── extraction/           # Field extraction providers
    │   ├── conversion/           # PDF/image conversion
    │   ├── validation/           # Validation rule engine
    │   ├── domain/               # Domain logic & IRDAI rules
    │   ├── workflow/
    │   │   └── policies.py       # Workflow & review policies
    │   │
    │   ├── security/             # Auth, RBAC, API keys
    │   │   ├── auth.py
    │   │   ├── jwt.py
    │   │   ├── apikey.py
    │   │   ├── rbac.py
    │   │   ├── crypto.py
    │   │   ├── oauth.py
    │   │   ├── secrets.py
    │   │   └── middleware.py     # Security headers middleware
    │   │
    │   ├── analytics/            # Analytics, cost tracking, reporting
    │   │   ├── aggregator.py
    │   │   ├── service.py
    │   │   ├── exports.py        # XLSX / PDF export
    │   │   ├── cost.py
    │   │   ├── sla.py
    │   │   └── statistics.py
    │   │
    │   ├── observability/        # Metrics, tracing, logging, circuit breakers
    │   │   ├── logging.py        # Structured JSON logging
    │   │   ├── metrics.py        # Prometheus metrics
    │   │   ├── tracing.py        # OpenTelemetry tracing
    │   │   ├── middleware.py     # Request lifecycle middleware
    │   │   ├── circuit_breaker.py
    │   │   ├── health.py
    │   │   └── readiness.py
    │   │
    │   ├── cache/                # Caching layer (in-memory / Redis)
    │   │   ├── provider.py
    │   │   └── keys.py
    │   │
    │   ├── storage/              # File storage abstraction (local / S3-ready)
    │   └── jobs/                 # Async job queue & workers
    │
    ├── tests/                    # pytest test suite
    ├── scripts/                  # Dev/ops utility scripts
    ├── kubernetes/               # Kubernetes manifests
    ├── helm/                     # Helm chart for K8s deployment
    ├── uploads/                  # Runtime: uploaded documents
    └── results/                  # Runtime: processing results (JSON)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- API key for at least one VLM provider (Gemini, OpenAI, or Ollama running locally)
- PostgreSQL (production) or SQLite (development, default)
- Redis (optional — required only for Redis-backed cache/rate limiting)

### Setup

```bash
# Clone the repo
git clone https://github.com/OnHighEngineer/krama_labs.git
cd krama_labs

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt
```

### Configuration

Create a `.env` file in `backend/` (see `.env.example`):

```env
# LLM Provider
LLM_PROVIDER=gemini               # gemini | openai | local
GEMINI_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here

# Database
DATABASE_URL=sqlite:///./krama_dev.db   # or postgres://...

# Security (change in production!)
JWT_SECRET=super-secret-key-change-in-production
ENABLE_AUTH=False                 # Set True to enforce auth

# Optional: Redis
REDIS_URL=redis://localhost:6379
ENABLE_REDIS=False

# Observability
ENABLE_METRICS=True
ENABLE_TRACING=False              # Set True + OTLP_ENDPOINT for distributed tracing
```

### Run

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

### Database Migrations

```bash
cd backend
# Apply all migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe change"
```

---

## API Endpoints

### Core (legacy-compatible `/api` and `/api/v1`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check & pipeline status |
| `GET` | `/api/doc-types` | List supported document types |
| `POST` | `/api/process` | Upload and process a document |
| `POST` | `/api/chat` | Chat with AI about processed results |
| `GET` | `/api/results/{job_id}` | Retrieve processing results |

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | Login and obtain JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `POST` | `/api/v1/auth/logout` | Logout and invalidate token |

### API Keys (`/api/v1/apikeys`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/apikeys` | Create a new API key |
| `GET` | `/api/v1/apikeys` | List API keys |
| `DELETE` | `/api/v1/apikeys/{key_id}` | Revoke an API key |

### Production V1 Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents` | Upload & submit document for processing |
| `GET` | `/api/v1/documents/{id}` | Get document status and results |
| `GET` | `/api/v1/jobs` | List async processing jobs |
| `GET` | `/api/v1/jobs/{job_id}/status` | Poll async job status |
| `GET` | `/api/v1/claims` | List claims |
| `POST` | `/api/v1/claims` | Create a claim |
| `GET` | `/api/v1/organizations` | List organizations |
| `GET` | `/api/v1/pages/{page_id}` | Get extracted page details |
| `GET` | `/api/v1/providers` | List LLM provider health |
| `POST` | `/api/v1/documents/{id}/review` | Submit human review decision |

### Observability

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/metrics` | Prometheus metrics scrape endpoint |
| `GET` | `/api/observability/status` | Observability subsystem status |

### Analytics & Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/summary` | Claim processing statistics |
| `GET` | `/api/v1/analytics/export` | Export analytics as XLSX or PDF |
| `GET` | `/api/v1/admin/...` | Admin operations |

### Process a Document (quick example)

```bash
curl -X POST http://localhost:8000/api/process \
  -F "file=@discharge_summary.pdf"
```

Returns structured JSON with extracted fields, confidence scores, validation results, and decision recommendation.

---

## How It Works

1. **Ingestion** — Files received via multipart upload. Size, type, and batch limits enforced. Chunked streaming for large files.
2. **Document Conversion** — PDFs rendered to images per page. Multi-page support. Pixel safety limits prevent memory exhaustion.
3. **OCR** — PaddleOCR extracts text regions with bounding boxes and confidence scores.
4. **Classification** — Identifies document type across 30+ types in 6 categories using rule-based or LLM classifier.
5. **Field Extraction** — Type-specific regex patterns + optional VLM extraction pass (Gemini / OpenAI / Ollama with configurable fallback chain).
6. **Triple Validation** — OCR results, VLM results, and structural patterns are cross-checked. Conflicts flagged. Fuzzy matching applied.
7. **Review Workflow** — Auto-approval above confidence threshold. Human-in-the-loop review queue for borderline cases. IRDAI policy checks.
8. **Fraud Detection** — Checks for inflated bills, date inconsistencies, and forged patterns.
9. **Decision** — Claims auto-approved, flagged, or rejected with reasons and full audit trail.
10. **Async Jobs** — Long-running documents submitted as async jobs. Retry with exponential backoff. Up to 4 concurrent workers.

---

## Observability

- **Metrics** — Prometheus counters/histograms for requests, processing stages, LLM latency, and errors. Scraped at `/api/metrics`.
- **Tracing** — OpenTelemetry spans exported via OTLP (Jaeger / Tempo compatible). Configure `OTLP_ENDPOINT`.
- **Logging** — Structured JSON logs with correlation IDs on every request.
- **Circuit Breakers** — Per-LLM-provider circuit breakers prevent cascading failures.
- **Readiness** — `/api/health` reports per-subsystem readiness (DB, cache, OCR engine, LLM providers).

---

## Security

- **JWT Authentication** — HS256 tokens with access (30 min) and refresh (7 day) expiry. Disabled by default; enable with `ENABLE_AUTH=True`.
- **API Key Auth** — Bearer-token API keys for programmatic access. Enable with `ENABLE_API_KEYS=True`.
- **RBAC** — Role-based access control. Enable with `ENABLE_RBAC=True`.
- **Security Headers** — HSTS, X-Frame-Options, CSP, and more via `SecurityHeadersMiddleware`.
- **Rate Limiting** — Per-IP/org rate limiting (100 req/60 s by default). Enable with `ENABLE_RATE_LIMIT=True`.

---

## Deployment

### Docker

```bash
# Build backend image
docker build -t krama-ai-backend ./backend

# Run
docker run -p 8000:8000 --env-file backend/.env krama-ai-backend
```

### Kubernetes / Helm

Helm chart and Kubernetes manifests are in `backend/helm/` and `backend/kubernetes/`.

```bash
helm upgrade --install krama-ai backend/helm/ -f values.yaml
```

### Vercel (Frontend)

The frontend (`index.html` + `assets/`) is deployed to Vercel.  
Configuration is in `vercel.json`. API calls are proxied to the backend.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `gemini` | Active LLM provider (`gemini`/`openai`/`local`) |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `DATABASE_URL` | `sqlite:///./krama_dev.db` | Database connection string |
| `REDIS_URL` | — | Redis URL (optional) |
| `JWT_SECRET` | *(change me)* | JWT signing secret |
| `ENABLE_AUTH` | `False` | Enable JWT authentication |
| `ENABLE_RATE_LIMIT` | `False` | Enable rate limiting |
| `ENABLE_METRICS` | `True` | Enable Prometheus metrics |
| `ENABLE_TRACING` | `True` | Enable OpenTelemetry tracing |
| `OTLP_ENDPOINT` | — | OTLP collector endpoint |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max file size per upload |
| `MAX_BATCH_FILES` | `20` | Max files per batch |
| `MAX_DOCUMENT_PAGES` | `500` | Max pages per document |
| `OCR_PROVIDER` | `paddle` | OCR engine provider |
| `AUTO_APPROVAL_THRESHOLD` | `0.95` | Confidence above which claims auto-approve |
| `CACHE_PROVIDER` | `inmemory` | Cache backend (`inmemory`/`redis`) |
| `DEPLOY_MODE` | `saas` | Deployment mode (`saas`/`onpremise`/`hybrid`) |

---

## Development & Testing

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_pipeline.py
```

---

## License

Proprietary. All rights reserved.

---

**Krama AI** — AI Claims Engine for Insurance  
[kramaai.com](https://kramaai.com) · Built for Indian Insurance
