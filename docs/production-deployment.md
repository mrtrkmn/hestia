# Production Deployment Guide

Step-by-step guide to deploy Hestia on a Linux server.

---

## Option A: Native Deployment (Recommended)

Best performance, no container overhead. Services run as systemd units.

### Prerequisites

- Ubuntu 22.04+ or Debian 12+ (fresh install recommended)
- At least 4 CPU cores, 8 GB RAM
- Root access
- A static IP or dynamic DNS for remote access

### Step 1: Install System Dependencies

```bash
sudo apt update && sudo apt install -y \
  python3.12 python3.12-venv python3-pip \
  nodejs npm \
  redis-server \
  ffmpeg \
  tesseract-ocr ocrmypdf \
  samba \
  wireguard \
  caddy \
  nftables
```

### Step 2: Clone Hestia

```bash
sudo git clone https://github.com/mrtrkmn/hestia.git /opt/hestia
cd /opt/hestia
```

### Step 3: Run the Install Script

```bash
sudo bash deploy/native/install.sh
```

This script performs all of the following automatically:

| Step | What it does |
|---|---|
| 1 | Creates system group `hub` and non-root users (`hub-api`, `hub-fileproc`, `hub-storage`, `hub-iot`, `hub-jobqueue`, `hub-worker`) |
| 2 | Creates Python virtualenv at `/opt/hestia/venv` and installs all pip dependencies |
| 3 | Generates cryptographic secrets (256-bit) and writes them to `/etc/hestia/secrets.env` with `chmod 600` |
| 4 | Copies config templates to `/etc/hestia/` and merges `hub.env` + `secrets.env` into per-service env files |
| 5 | Installs systemd unit files to `/etc/systemd/system/` |
| 6 | Applies firewall rules: only ports 80, 443, 51820 are exposed |
| 7 | Enables and starts all services |

### Step 4: Verify

```bash
# Check all services are running
sudo systemctl status hub-api-gateway hub-file-processor hub-job-queue hub-worker@1

# Test health endpoint
curl -k https://localhost/healthz
# → {"status":"ok"}

# View logs
sudo journalctl -u hub-api-gateway -f
```

The Hub should be healthy within 120 seconds.

### Step 5: Configure Domain (Optional)

Edit `/etc/hestia/hub.env`:

```bash
HUB_DOMAIN=hestia.yourdomain.com
```

If you have a public domain, Caddy will automatically obtain a Let's Encrypt certificate. For local-only use, the default self-signed cert works.

Restart Caddy:
```bash
sudo systemctl restart caddy
```

### Step 6: Build and Serve the Dashboard

```bash
cd /opt/hestia/dashboard
npm install --production
npm run build
# Built files are in dashboard/dist/ — Caddy serves them at /
```

### Step 7: Set Up WireGuard VPN (Optional)

```bash
# Generate server keys
wg genkey | tee /etc/wireguard/server_private | wg pubkey > /etc/wireguard/server_public

# Edit the config
sudo nano /opt/hestia/config/wireguard/wg0.conf
# Replace <SERVER_PRIVATE_KEY> with contents of /etc/wireguard/server_private

# Add a client peer
# [Peer]
# PublicKey = <client-public-key>
# PresharedKey = <preshared-key>
# AllowedIPs = 10.100.0.2/32

# Copy config and start
sudo cp /opt/hestia/config/wireguard/wg0.conf /etc/wireguard/
sudo systemctl enable --now wg-quick@wg0

# Forward port 51820/UDP on your router to this machine
```

### Step 8: Enable Optional Features

Edit `/etc/hestia/hub.env` and restart services:

```bash
# Enable ZFS (requires ZFS installed: sudo apt install zfsutils-linux)
HUB_ENABLE_ZFS=true

# Enable NFS (requires nfs-kernel-server)
HUB_ENABLE_NFS=true

# Enable Nextcloud
HUB_ENABLE_NEXTCLOUD=true

# Enable Tailscale (requires tailscale installed)
HUB_ENABLE_TAILSCALE=true
```

```bash
# Restart all services to pick up changes
sudo systemctl restart hub-api-gateway hub-file-processor hub-job-queue hub-worker@1
```

### Step 9: Scale Workers

```bash
# Start additional workers
sudo systemctl enable --now hub-worker@2
sudo systemctl enable --now hub-worker@3

# Verify they're receiving jobs (within 10 seconds)
sudo journalctl -u hub-worker@2 -f
```

### Step 10: Create First Admin User

Access `https://localhost` (or your domain) and log in through Authelia. The first user is configured in `/opt/hestia/config/authelia/users_database.yml`.

To generate a password hash:
```bash
docker run --rm authelia/authelia:4 authelia crypto hash generate argon2 --password 'YourSecurePassword123!'
```

Add to `users_database.yml`:
```yaml
users:
  admin:
    displayname: "Admin"
    password: "$argon2id$v=19$m=65536,t=3,p=4$..."
    email: admin@localhost
    groups:
      - admin
```

---

## Option B: Docker Compose Deployment

Simpler setup, all services containerized.

### Prerequisites

- Docker Engine 24+
- Docker Compose v2
- At least 4 CPU cores, 8 GB RAM

### Step 1: Clone and Configure

```bash
git clone https://github.com/mrtrkmn/hestia.git
cd hestia/deploy/docker

cp .env.example .env
nano .env
```

Edit `.env`:
```
HUB_DOMAIN=localhost
HUB_SECRET_KEY=generate-a-random-64-char-string-here
HUB_REDIS_URL=redis://redis:6379/0
```

Generate a secret:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 2: Start Everything

```bash
docker compose up -d
```

Services start in dependency order:
1. Redis (with health check)
2. Authelia
3. API Gateway, File Processor, Job Queue, Worker, Storage, IoT Bridge
4. Caddy (reverse proxy)
5. Dashboard

### Step 3: Verify

```bash
# Check all containers
docker compose ps

# Check logs
docker compose logs -f api-gateway

# Health check
curl -k https://localhost/healthz
```

### Step 4: Scale Workers

```bash
docker compose up -d --scale worker=4
```

### Step 5: Manage Data

All data persists in named Docker volumes:

| Volume | Contents |
|---|---|
| `redis_data` | Job queue state |
| `uploads` | Uploaded files |
| `outputs` | Processed files |
| `storage_data` | NAS share data |
| `authelia_data` | User database |
| `caddy_data` | TLS certificates |
| `mosquitto_data` | MQTT broker data |

Backup:
```bash
docker compose stop
docker run --rm -v hestia_storage_data:/data -v $(pwd):/backup alpine tar czf /backup/storage-backup.tar.gz /data
docker compose start
```

---

## Post-Deployment Checklist

- [ ] Access `https://your-domain` and verify the dashboard loads
- [ ] Log in through Authelia
- [ ] Check service health on the Dashboard page (all green)
- [ ] Upload a test PDF and run OCR
- [ ] Create a Samba share and access it from another device
- [ ] (Optional) Connect via WireGuard from outside the network
- [ ] (Optional) Set up an MQTT automation with a test topic
- [ ] Verify firewall: `nmap -p 1-65535 your-server-ip` should only show 80, 443, 51820

## Monitoring

```bash
# Native: view service logs
sudo journalctl -u hub-api-gateway --since "1 hour ago"

# Docker: view logs
docker compose logs --tail 100 api-gateway

# Check disk usage
df -h /srv/storage

# Check Redis queue depth
redis-cli LLEN hestia:queue:normal
```

## Updating

### Native
```bash
cd /opt/hestia
sudo git pull
sudo /opt/hestia/venv/bin/pip install -r shared/requirements.txt
sudo systemctl restart hub-api-gateway hub-file-processor hub-job-queue hub-worker@1
```

### Docker
```bash
cd deploy/docker
docker compose pull
docker compose up -d
```
