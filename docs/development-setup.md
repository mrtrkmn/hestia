# Development Setup Guide

Step-by-step guide to get Hestia running locally for development.

---

## Prerequisites

- Python 3.12+
- Node.js 18+
- Redis 7+ (or use fakeredis for tests)
- Git

## Step 1: Clone the Repository

```bash
git clone git@github.com:mrtrkmn/hestia.git
cd hestia
```

## Step 2: Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate

# Core dependencies
pip install -r shared/requirements.txt
pip install -r job-queue/requirements.txt
pip install -r file-processor/requirements.txt

# FastAPI + server
pip install fastapi uvicorn httpx python-multipart

# Test dependencies
pip install fakeredis pytest pytest-asyncio hypothesis
```

## Step 3: Dashboard Dependencies

```bash
cd dashboard
npm install
cd ..
```

## Step 4: Start Redis

Option A — Local Redis:
```bash
redis-server
```

Option B — Docker:
```bash
docker run -d --name hestia-redis -p 6379:6379 redis:7-alpine
```

Option C — Skip Redis entirely (tests use fakeredis, no Redis needed).

## Step 5: Run Services Individually

Open separate terminals for each service:

```bash
# Terminal 1: API Gateway (port 8000)
cd api-gateway
uvicorn app.main:app --reload --port 8000

# Terminal 2: File Processor (port 8001)
cd file-processor
uvicorn app.main:app --reload --port 8001

# Terminal 3: Job Queue API (port 8004)
cd job-queue
uvicorn app.main:app --reload --port 8004

# Terminal 4: Worker
cd job-queue
python -m app.worker

# Terminal 5: Dashboard (port 5173)
cd dashboard
npm run dev
```

The dashboard proxies `/api` requests to `localhost:8000` (configured in `vite.config.ts`).

## Step 6: Verify Everything Works

```bash
# Health check
curl http://localhost:8000/healthz
# → {"status":"ok"}

# OpenAPI docs
open http://localhost:8000/api/docs

# Dashboard
open http://localhost:5173
```

## Step 7: Run Tests

```bash
# All Python tests (from project root)
python -m pytest shared/ job-queue/ -v

# API Gateway
cd api-gateway && python -m pytest tests/ -v

# File Processor
cd file-processor && python -m pytest tests/ -v

# Storage Service
cd storage-service && python -m pytest tests/ -v

# IoT Bridge
cd iot-bridge && python -m pytest tests/ -v

# Dashboard
cd dashboard && npm test
```

## Environment Variables

For development, defaults work out of the box. Override with environment variables:

```bash
export HUB_SECRET_KEY="dev-secret-key-at-least-32-chars!!"
export HUB_REDIS_URL="redis://localhost:6379/0"
export HUB_LOG_LEVEL="DEBUG"
```

Or create a `.env` file in the project root (it's gitignored):

```
HUB_SECRET_KEY=dev-secret-key-at-least-32-chars!!
HUB_REDIS_URL=redis://localhost:6379/0
HUB_LOG_LEVEL=DEBUG
```

## Project Layout for Developers

```
hestia/
├── shared/               ← Start here. Models, config, auth used by all services
│   ├── config.py         ← HubSettings (env vars, ports, feature flags)
│   ├── models/           ← Pydantic models shared across services
│   ├── auth/             ← JWT, TOTP, RBAC, password policy, MQTT credentials
│   └── security.py       ← Secret generation, structured logging
├── api-gateway/app/
│   ├── main.py           ← FastAPI app, middleware registration
│   ├── middleware/        ← JWT auth, input sanitization, rate limiting
│   └── routes/           ← One file per resource (files, jobs, pipelines, etc.)
├── file-processor/app/
│   ├── processors/       ← pdf.py, image.py, media.py
│   └── pipeline.py       ← Batch pipeline engine
├── job-queue/app/
│   ├── queue.py          ← Redis queue operations
│   └── worker.py         ← Background worker process
├── storage-service/app/  ← Samba, NFS, ZFS, Nextcloud managers
├── iot-bridge/app/       ← MQTT, Home Assistant, automation engine
└── dashboard/src/
    ├── pages/            ← One page per feature
    ├── api/client.ts     ← Axios client with JWT interceptor
    └── hooks/            ← React hooks (useJobs, etc.)
```

## Common Development Tasks

### Add a new API endpoint

1. Add route in `api-gateway/app/routes/<resource>.py`
2. Add Pydantic model in `shared/models/` if needed
3. The route is automatically versioned under `/api/v1/`

### Add a new file processing operation

1. Add function in `file-processor/app/processors/<type>.py`
2. Add format mapping in `file-processor/app/pipeline.py` → `FORMAT_MAP`
3. Add property test in `file-processor/tests/`

### Add a new dashboard page

1. Create `dashboard/src/pages/NewPage.tsx`
2. Add route in `dashboard/src/App.tsx`
3. Add nav link in the `<nav>` section

### Debug a failing test

```bash
# Run single test with verbose output
python -m pytest shared/tests/test_jwt_roundtrip.py -v -s

# Run with Hypothesis debug output
python -m pytest shared/tests/test_password_policy.py -v --hypothesis-show-statistics
```
