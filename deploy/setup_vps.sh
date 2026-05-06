#!/usr/bin/env bash
# Setup una-tantum per la VPS Linux.
# Esegui con: sudo bash deploy/setup_vps.sh /home/ubuntu/claude-of-control /home/ubuntu/venv312

set -e

PROJECT_DIR="${1:-/home/ubuntu/claude-of-control}"
VENV_DIR="${2:-/home/ubuntu/venv312}"
SERVICE_SRC="$PROJECT_DIR/deploy/barsport.service"
SERVICE_DST="/etc/systemd/system/barsport.service"
LOG_DIR="/var/log/barsport"

echo "=== [1/5] Installazione Chromium ==="
apt-get update -qq
apt-get install -y chromium-browser

echo "=== [2/5] Installazione dipendenze Python ==="
"$VENV_DIR/bin/pip" install --quiet apscheduler drissionpage sqlalchemy psycopg2-binary

echo "=== [3/5] Creazione directory log ==="
mkdir -p "$LOG_DIR"
chown ubuntu:ubuntu "$LOG_DIR"

echo "=== [4/5] Installazione systemd service ==="
sed "s|/home/ubuntu/claude-of-control|$PROJECT_DIR|g; s|/home/ubuntu/venv312|$VENV_DIR|g" \
    "$SERVICE_SRC" > "$SERVICE_DST"

systemctl daemon-reload
systemctl enable barsport
systemctl start barsport

echo "=== [5/5] Setup completato ==="
echo "Stato servizio:"
systemctl status barsport --no-pager

echo ""
echo "Per seguire i log in tempo reale:"
echo "  tail -f $LOG_DIR/scheduler.log"
