#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="/etc/thedetect/thedetect.env"
PYTHON_BIN="${PYTHON_BIN:-/home/cskang/miniconda3/envs/dj5/bin/python}"
PUBLIC_DOMAIN="${THEDETECT_PUBLIC_DOMAIN:-detect.thesysm.com}"

cd "$ROOT_DIR"

sudo -v

echo "[1/4] Refreshing production env file"

secret_key="$("$PYTHON_BIN" -c 'import secrets; print(secrets.token_urlsafe(50))')"
tmp_env="$(mktemp)"
cat > "$tmp_env" <<EOF
SECRET_KEY=${secret_key}
DEBUG=false
ALLOWED_HOSTS=${PUBLIC_DOMAIN}
CSRF_TRUSTED_ORIGINS=https://${PUBLIC_DOMAIN}
SERVICE_BASE_URL=https://${PUBLIC_DOMAIN}
DJANGO_SETTINGS_MODULE=theDetect.settings
APP_VERSION=prod
APP_BUILD_SHA=manual
READINESS_CHECK_MIGRATIONS=1
STATIC_URL=/static/
STATIC_ROOT=${ROOT_DIR}/staticfiles
MEDIA_URL=/media/
MEDIA_ROOT=${ROOT_DIR}/project_data
PROJECT_DATA_DIR=${ROOT_DIR}/project_data
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_HSTS_PRELOAD=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
USE_X_FORWARDED_HOST=true
EOF

if sudo test -f "$ENV_FILE"; then
  sudo cp "$ENV_FILE" "$ENV_FILE.bak.$(date +%Y%m%d%H%M%S)"
fi

sudo mkdir -p /etc/thedetect
sudo install -m 640 -o root -g cskang "$tmp_env" "$ENV_FILE"
rm -f "$tmp_env"

echo "[2/4] Installing deployment files"
bash deploy/production/install_thedetect.sh

echo "[3/4] Validating deployment"
bash deploy/production/validate_thedetect.sh

echo "[4/4] Completed"
echo "Production URL: https://${PUBLIC_DOMAIN}"
