#!/usr/bin/env bash
set -euo pipefail

# Hestia — Native Install Script
# Requirements: 14.2, 15.2, 15.3, 15.6, 15.10

HUB_DIR="/opt/hestia"
CONFIG_DIR="/etc/hestia"
SYSTEMD_DIR="/etc/systemd/system"

echo "=== Hestia Installer ==="

# 1. Create system users
echo "[1/7] Creating system users..."
for u in hub-api hub-fileproc hub-storage hub-iot hub-jobqueue hub-worker; do
    id "$u" &>/dev/null || useradd --system --no-create-home --shell /usr/sbin/nologin -g hub "$u"
done
getent group hub &>/dev/null || groupadd --system hub

# 2. Install to /opt
echo "[2/7] Deploying application..."
mkdir -p "$HUB_DIR" "$CONFIG_DIR"
cp -r . "$HUB_DIR/"
python3 -m venv "$HUB_DIR/venv"
"$HUB_DIR/venv/bin/pip" install -r "$HUB_DIR/shared/requirements.txt"
for svc in api-gateway file-processor storage-service iot-bridge job-queue; do
    "$HUB_DIR/venv/bin/pip" install -r "$HUB_DIR/$svc/requirements.txt" 2>/dev/null || true
done

# 3. Generate secrets
echo "[3/7] Generating deployment secrets..."
"$HUB_DIR/venv/bin/python" -c "
from shared.security import generate_deployment_secrets
secrets = generate_deployment_secrets()
for k, v in secrets.items():
    print(f'HUB_{k.upper()}={v}')
" > "$CONFIG_DIR/secrets.env"
chmod 600 "$CONFIG_DIR/secrets.env"

# 4. Deploy config
echo "[4/7] Deploying configuration..."
cp deploy/native/config/hub.env "$CONFIG_DIR/hub.env"
for svc in api-gateway file-processor storage-service iot-bridge job-queue worker; do
    cat "$CONFIG_DIR/hub.env" "$CONFIG_DIR/secrets.env" > "$CONFIG_DIR/$svc.env"
done

# 5. Install systemd units
echo "[5/7] Installing systemd units..."
cp deploy/native/systemd/*.service "$SYSTEMD_DIR/"
systemctl daemon-reload

# 6. Firewall rules — only expose 80, 443, 51820
echo "[6/7] Applying firewall rules..."
if command -v nft &>/dev/null; then
    nft flush ruleset
    nft add table inet hub_filter
    nft add chain inet hub_filter input '{ type filter hook input priority 0; policy drop; }'
    nft add rule inet hub_filter input iif lo accept
    nft add rule inet hub_filter input ct state established,related accept
    nft add rule inet hub_filter input tcp dport '{80, 443}' accept
    nft add rule inet hub_filter input udp dport 51820 accept
elif command -v iptables &>/dev/null; then
    iptables -F
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    iptables -A INPUT -p udp --dport 51820 -j ACCEPT
    iptables -A INPUT -j DROP
fi

# 7. Enable and start services
echo "[7/7] Starting services..."
SERVICES=(hub-api-gateway hub-file-processor hub-job-queue hub-worker@1)
for svc in "${SERVICES[@]}"; do
    systemctl enable --now "$svc"
done

echo "=== Installation complete ==="
echo "Hub should be healthy within 120 seconds."
