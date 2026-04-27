#!/bin/bash
# ============================================================
# Ubuntu Server Setup Script
# ============================================================
# Run this once on a fresh Ubuntu server to set up everything.
#
# Usage:
#   chmod +x scripts/setup_ubuntu.sh
#   sudo ./scripts/setup_ubuntu.sh
# ============================================================

set -e

APP_DIR="/opt/services/wrams"
APP_USER="www-data"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  WRAMS Modular Service — Ubuntu Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# --- 1. System packages ---
echo "[1/7] Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv nginx postgresql-client

# --- 2. Create application directory ---
echo "[2/7] Setting up application directory..."
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/frames_storage"

# Copy project files (skip venv, .git, etc.)
echo "  Copying project files to $APP_DIR..."
rsync -av --exclude='venv' --exclude='.git' --exclude='__pycache__' \
    --exclude='main_service' --exclude='test videos' --exclude='*.jar' \
    --exclude='brain' --exclude='*.db' \
    "$(dirname "$(dirname "$(readlink -f "$0")")")/" "$APP_DIR/"

# --- 3. Python virtual environment ---
echo "[3/7] Creating Python virtual environment..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip -q
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

# --- 4. Environment file ---
echo "[4/7] Setting up environment..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "  ⚠️  Created .env from template. EDIT IT with your production values:"
    echo "     sudo nano $APP_DIR/.env"
else
    echo "  .env already exists, skipping."
fi

# --- 5. File permissions ---
echo "[5/7] Setting permissions..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chmod 600 "$APP_DIR/.env"

# --- 6. Systemd services ---
echo "[6/7] Installing systemd services..."
cp "$APP_DIR/deploy/vision-player.service" /etc/systemd/system/
cp "$APP_DIR/deploy/asset-filter.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable vision-player asset-filter

# --- 7. Nginx ---
echo "[7/7] Configuring nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/wrams
ln -sf /etc/nginx/sites-available/wrams /etc/nginx/sites-enabled/wrams

# Remove default site if it exists
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Edit config:     sudo nano $APP_DIR/.env"
echo "  2. Edit nginx:      sudo nano /etc/nginx/sites-available/wrams"
echo "  3. Start services:  sudo systemctl start vision-player asset-filter"
echo "  4. Check status:    sudo systemctl status vision-player asset-filter"
echo "  5. View logs:       sudo journalctl -u vision-player -f"
echo ""
