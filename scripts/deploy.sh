#!/usr/bin/env bash
# ============================================================
# deploy.sh — Deploy Siphon to VPS with SSL
# Run from the VPS after cloning the repo
# Usage: bash scripts/deploy.sh
# ============================================================
set -euo pipefail

DOMAIN="siphon.site"
EMAIL="admin@siphon.site"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"

echo "=== Siphon Deploy ==="
echo "Domain: $DOMAIN"
echo "Project: $PROJECT_DIR"
echo ""

# 1. Ensure secrets exist
if [ ! -f secrets/yt_cookies.txt ]; then
  echo "ERROR: secrets/yt_cookies.txt not found."
  echo "Upload it from your local machine first:"
  echo "  scp secrets/yt_cookies.txt root@VPS_IP:$PROJECT_DIR/secrets/"
  exit 1
fi

# 2. Ensure Docker is available
if ! command -v docker &> /dev/null; then
  echo "ERROR: Docker not found. Install Docker first."
  exit 1
fi

# 3. Start with HTTP-only nginx first (for certbot challenge)
echo "→ Step 1: Starting services with temporary HTTP config..."

# Create temp HTTP-only nginx conf for cert generation
cat > /tmp/nginx-temp.conf <<'NGINX'
server {
    listen 80;
    server_name siphon.site www.siphon.site;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
NGINX

# Build and start with temp config
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Override nginx config for initial cert generation
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d redis backend worker
docker compose -f docker-compose.yml -f docker-compose.prod.yml run -d \
  --name siphon-frontend-temp \
  -p 80:80 \
  -v /tmp/nginx-temp.conf:/etc/nginx/conf.d/default.conf:ro \
  -v siphon_certbot_webroot:/var/www/certbot:ro \
  frontend

echo "→ Waiting for nginx to start..."
sleep 5

# 4. Get SSL certificate
echo "→ Step 2: Obtaining SSL certificate from Let's Encrypt..."
docker run --rm \
  -v siphon_certbot_webroot:/var/www/certbot \
  -v siphon_certbot_certs:/etc/letsencrypt \
  certbot/certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal

# 5. Stop temp container and switch to full SSL config
echo "→ Step 3: Switching to SSL configuration..."
docker stop siphon-frontend-temp 2>/dev/null || true
docker rm siphon-frontend-temp 2>/dev/null || true
rm -f /tmp/nginx-temp.conf

# 6. Start everything with production SSL config
echo "→ Step 4: Starting all services with SSL..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo ""
echo "============================================"
echo "  ✓ Siphon deployed successfully!"
echo "  https://$DOMAIN"
echo "============================================"
echo ""
echo "Useful commands:"
echo "  Logs:    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "  Restart: docker compose -f docker-compose.yml -f docker-compose.prod.yml restart"
echo "  Stop:    docker compose -f docker-compose.yml -f docker-compose.prod.yml down"
