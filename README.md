# Hestia

[![tests](https://github.com/mrtrkmn/hestia/actions/workflows/tests.yml/badge.svg)](https://github.com/mrtrkmn/hestia/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*Named after the Greek goddess of the hearth — the sacred fire at the center of every household that all other functions gathered around.*

A self-hosted, fully local platform that unifies file processing, network-attached storage, secure networking, IoT integration, and a job queue behind a single web dashboard. Zero cloud dependencies — everything runs on one Linux machine.

## Architecture

```
Browser/Client ──HTTPS──▶ Caddy (Reverse Proxy, TLS)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
          Dashboard      API Gateway      Authelia (SSO)
          (React SPA)    (FastAPI)        (OIDC, 2FA)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        File Processor   Storage Service   IoT Bridge
        (PDF/Image/AV)   (Samba/NFS/ZFS)   (HA + MQTT)
              │
        Job Queue + Workers (Redis)

Remote Client ──WireGuard──▶ VPN Gateway (port 51820)
```

All services communicate over localhost. Redis handles async job dispatch. Caddy terminates TLS with auto-generated self-signed certs.

## Project Structure

```
hestia/
├── api-gateway/          # FastAPI — central API routing, JWT auth, rate limiting
├── file-processor/       # PDF merge/split/OCR/compress, image conversion, AV transcode
├── storage-service/      # Samba/NFS share management, ZFS snapshots, optional Nextcloud
├── iot-bridge/           # Home Assistant + Mosquitto MQTT, automation workflows
├── job-queue/            # Redis-backed queue, worker processes, job REST API
├── dashboard/            # React + TypeScript + Vite SPA
├── shared/               # Pydantic models, config, auth (JWT/TOTP/RBAC), security utils
├── config/               # Caddy, Authelia, WireGuard, Mosquitto configs
└── deploy/
    ├── native/           # systemd units, install script, firewall rules
    └── docker/           # docker-compose.yml, .env.example
```

## Prerequisites

### Native Mode (default)

- Linux (Ubuntu 22.04+ / Debian 12+ recommended)
- Python 3.12+
- Node.js 18+ (for dashboard build)
- Redis 7+
- FFmpeg (for video/audio transcoding)
- Tesseract + ocrmypdf (for PDF OCR)
- Samba (for SMB shares)
- WireGuard (for VPN)
- Caddy 2+ (for reverse proxy)

### Docker Mode (alternative)

- Docker Engine 24+
- Docker Compose v2

## Quick Start — Native Mode

```bash
git clone <repo-url> /opt/hestia
cd /opt/hestia
sudo bash deploy/native/install.sh
```

The install script will:

1. Create dedicated non-root system users for each service
2. Set up a Python virtualenv and install all dependencies
3. Generate cryptographically random secrets (256-bit entropy)
4. Deploy config files to `/etc/hestia/`
5. Install and enable systemd units
6. Apply firewall rules (only ports 80, 443, 51820 exposed)
7. Start all services

The Hub should be healthy within 120 seconds. Access it at `https://localhost`.

## Quick Start — Docker Mode

```bash
cd deploy/docker
cp .env.example .env
# Edit .env with your settings
docker compose up -d
```

All services start in dependency order with health checks. Data persists in named Docker volumes.

## Development Setup

### Backend (Python)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r shared/requirements.txt
pip install -r job-queue/requirements.txt
pip install -r file-processor/requirements.txt
pip install fastapi uvicorn httpx python-multipart
pip install fakeredis pytest pytest-asyncio hypothesis
```

### Dashboard (TypeScript)

```bash
cd dashboard
npm install
npm run dev   # starts Vite dev server on :5173
```

### Running Individual Services

```bash
# API Gateway
cd api-gateway && uvicorn app.main:app --port 8000

# File Processor
cd file-processor && uvicorn app.main:app --port 8001

# Job Queue API
cd job-queue && uvicorn app.main:app --port 8004

# Worker
cd job-queue && python -m app.worker
```

## Running Tests

The test suite includes 126 tests covering 30 correctness properties using Hypothesis (Python) and fast-check (TypeScript) for property-based testing.

```bash
# Shared + Job Queue (from project root)
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

## Services

### API Gateway (port 8000)

Central HTTP entry point. All endpoints versioned under `/api/v1/`.

- JWT authentication — 401 for missing/invalid/expired tokens
- Input sanitization — SQL injection, XSS, path traversal detection
- Rate limiting — 100 req/min per user (configurable)
- OpenAPI 3.0 spec at `/api/docs`

### File Processor (port 8001)

- **PDF**: merge, split, OCR (Tesseract), compress (pikepdf)
- **Image**: PDF↔PNG↔JPEG conversion with format validation
- **Media**: video (MP4/MKV/AVI/WebM) and audio (MP3/FLAC/WAV/AAC/OGG) transcoding via FFmpeg
- Corrupt/unsupported files return structured errors with filename and reason

### Batch Pipeline Engine

Chain multiple file operations (e.g., OCR → compress → convert to PNG):

- Validates format compatibility between steps before execution
- Executes sequentially, piping output to next step
- Preserves completed outputs on failure
- Named pipeline definitions saved/loaded from disk

### Job Queue (port 8004) + Workers

- Redis-backed FIFO queue with priority levels (low, normal, high)
- Unique job ID returned within 1 second
- Workers report progress every ≤5 seconds
- Crash detection (30s heartbeat) with auto-retry (up to 3x)
- Job metadata retained 7 days

### Storage Service (port 8002)

- Samba (SMB) shares for Windows/macOS/Linux
- Optional NFS exports for Linux/macOS
- Optional ZFS datasets with checksumming, compression, snapshots
- Per-user/per-share access control (admin bypasses all)
- Optional Nextcloud integration for WebDAV and file sync

### IoT Bridge (port 8003)

- Home Assistant instance management
- Mosquitto MQTT broker with authenticated connections
- Automation workflows triggered by MQTT topic patterns or cron schedules
- Retry failed actions 3x with exponential backoff
- Full execution logging (timestamp, trigger, actions, status)

### Auth Service (Authelia, port 9091)

- SSO via OpenID Connect across all services
- TOTP two-factor authentication (opt-in per user)
- JWT tokens with configurable expiry (default 1 hour)
- Password policy: min 12 chars, upper + lower + digit + special
- Account lockout: 5 failures in 10 min → 15 min lock
- RBAC with `admin` and `user` roles

### Dashboard (port 5173 dev / served via Caddy in production)

- React SPA with React Router
- File upload with drag-and-drop (react-dropzone), up to 10 GB
- Real-time job progress polling
- Service health catalog refreshed every 30s
- Admin panel for user/role management
- Responsive layout: 320px to 2560px

## API Reference

All endpoints require `Authorization: Bearer <token>` except `/auth/*`, `/api/docs`, `/healthz`.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/files/upload` | Upload files |
| POST | `/api/v1/files/process` | Submit processing job |
| GET | `/api/v1/files/{id}` | File metadata |
| GET | `/api/v1/files/{id}/download` | Download processed file |
| GET | `/api/v1/jobs` | List jobs (filterable by status) |
| GET | `/api/v1/jobs/{id}` | Job status and details |
| DELETE | `/api/v1/jobs/{id}` | Cancel pending job |
| POST | `/api/v1/pipelines` | Create and execute pipeline |
| GET | `/api/v1/pipelines` | List saved pipelines |
| GET | `/api/v1/pipelines/{id}` | Get pipeline definition |
| PUT | `/api/v1/pipelines/{id}` | Update pipeline |
| DELETE | `/api/v1/pipelines/{id}` | Delete pipeline |
| GET | `/api/v1/storage/shares` | List NAS shares |
| POST | `/api/v1/storage/shares` | Create share |
| PUT | `/api/v1/storage/shares/{id}` | Update share |
| DELETE | `/api/v1/storage/shares/{id}` | Delete share |
| POST | `/api/v1/storage/snapshots` | Create ZFS snapshot |
| POST | `/api/v1/storage/snapshots/{id}/restore` | Restore snapshot |
| GET | `/api/v1/iot/entities` | List Home Assistant entities |
| GET | `/api/v1/iot/entities/{id}` | Get entity state |
| GET | `/api/v1/iot/automations` | List automation workflows |
| POST | `/api/v1/iot/automations` | Create automation |
| PUT | `/api/v1/iot/automations/{id}` | Update automation |
| DELETE | `/api/v1/iot/automations/{id}` | Delete automation |
| GET | `/api/v1/services/health` | All service statuses |
| GET | `/api/v1/admin/users` | List users (admin only) |
| POST | `/api/v1/admin/users` | Create user (admin only) |
| PUT | `/api/v1/admin/users/{id}` | Update user (admin only) |
| DELETE | `/api/v1/admin/users/{id}` | Delete user (admin only) |
| GET | `/api/v1/admin/logs` | System logs (admin only) |
| GET | `/api/docs` | OpenAPI 3.0 specification |
| GET | `/healthz` | Health check |

### Error Responses

All errors follow a consistent JSON format:

```json
{
  "error": "validation_error",
  "message": "Page range 5-20 exceeds document page count of 12",
  "field": "page_range"
}
```

| Code | Meaning |
|---|---|
| 400 | Validation error (field name + description in body) |
| 401 | Missing/invalid/expired JWT |
| 403 | Insufficient role |
| 404 | Resource not found |
| 422 | Unprocessable file (corrupt, unsupported codec, format mismatch) |
| 429 | Rate limit exceeded (`Retry-After` header included) |

## Configuration

### Native Mode

All config lives in `/etc/hestia/`:

| File | Purpose |
|---|---|
| `hub.env` | Ports, domain, feature flags |
| `secrets.env` | Auto-generated secrets (600 permissions) |
| `<service>.env` | Per-service env (merged from hub.env + secrets.env) |

### Docker Mode

Edit `deploy/docker/.env`:

```env
HUB_DOMAIN=localhost
HUB_SECRET_KEY=your-secret-here
HUB_REDIS_URL=redis://redis:6379/0
```

### Feature Flags

| Variable | Default | Description |
|---|---|---|
| `HUB_ENABLE_NEXTCLOUD` | `false` | Deploy local Nextcloud instance |
| `HUB_ENABLE_NFS` | `false` | Enable NFS exports |
| `HUB_ENABLE_ZFS` | `false` | Enable ZFS dataset management |
| `HUB_ENABLE_TAILSCALE` | `false` | Enable Tailscale mesh VPN |

### Service Ports

| Service | Port |
|---|---|
| Caddy (HTTP) | 80 |
| Caddy (HTTPS) | 443 |
| API Gateway | 8000 |
| File Processor | 8001 |
| Storage Service | 8002 |
| IoT Bridge | 8003 |
| Job Queue API | 8004 |
| Authelia | 9091 |
| WireGuard VPN | 51820 (UDP) |

## Security

Hestia follows zero-trust principles by default:

- All external traffic encrypted via TLS (Caddy with self-signed certs from local CA)
- Unique 256-bit secrets generated at install time
- All services run as dedicated non-root system users
- Firewall exposes only ports 80, 443, 51820 externally
- Redis, MQTT internal, and database ports are never externally accessible
- VPN clients restricted to Hub services only — no lateral LAN access
- Input sanitization on all API endpoints (SQL injection, XSS, path traversal)
- Rate limiting at 100 req/min per authenticated user
- Structured JSON logging for all security events (failed login, permission denied, config changes)
- Docker containers run as non-root with read-only root filesystems where possible

## Scaling Workers

### Native

```bash
sudo systemctl start hub-worker@2
sudo systemctl start hub-worker@3
# New workers begin receiving jobs within 10 seconds
```

### Docker

```bash
docker compose up -d --scale worker=4
```

## Remote Access

### WireGuard

1. Edit `config/wireguard/wg0.conf` — add peer blocks with client public keys
2. Start: `systemctl start wg-quick@wg0`
3. Clients connect on UDP port 51820
4. VPN clients can only reach Hub services, not other LAN devices

### Tailscale (optional)

Set `HUB_ENABLE_TAILSCALE=true` and run `tailscale up` on the Hub machine for zero-config mesh VPN.

## License

MIT
