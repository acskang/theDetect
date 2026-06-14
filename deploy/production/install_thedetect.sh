#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="/etc/thedetect/thedetect.env"
PYTHON_BIN="${PYTHON_BIN:-/home/cskang/miniconda3/envs/dj5/bin/python}"
PUBLIC_DOMAIN="${THEDETECT_PUBLIC_DOMAIN:-detect.thesysm.com}"
CLOUDFLARED_TUNNEL_NAME="${CLOUDFLARED_TUNNEL_NAME:-detect}"
CLOUDFLARED_TUNNEL_CRED_FILE="${CLOUDFLARED_TUNNEL_CRED_FILE:-/etc/cloudflared/detect-credentials.json}"
CLOUDFLARED_TUNNEL_CONFIG="${CLOUDFLARED_TUNNEL_CONFIG:-/etc/cloudflared/detect.yml}"
CLOUDFLARED_ORIGIN_CERT="${CLOUDFLARED_ORIGIN_CERT:-/etc/cloudflared/cert.pem}"

cd "$ROOT_DIR"

sudo -v

sudo mkdir -p /etc/thedetect /var/www/thedetect /logs/thedetect /etc/cloudflared
sudo chown cskang:www-data /logs/thedetect
sudo chmod 775 /logs/thedetect

mkdir -p "$ROOT_DIR/staticfiles" "$ROOT_DIR/project_data"
sudo chown -R cskang:www-data "$ROOT_DIR/staticfiles" "$ROOT_DIR/project_data"
sudo chmod -R u+rwX,g+rwX "$ROOT_DIR/staticfiles" "$ROOT_DIR/project_data"

if [ ! -f "$ENV_FILE" ]; then
  secret_key="$("$PYTHON_BIN" - <<'PY'
import secrets
print(secrets.token_urlsafe(50))
PY
)"
  tmp_env="$(mktemp)"
  cat > "$tmp_env" <<EOF
SECRET_KEY=${secret_key}
DEBUG=false
ALLOWED_HOSTS=${PUBLIC_DOMAIN}
CSRF_TRUSTED_ORIGINS=https://${PUBLIC_DOMAIN}
SERVICE_BASE_URL=https://${PUBLIC_DOMAIN}
DJANGO_SETTINGS_MODULE=theDetect.settings
APP_VERSION=prod
APP_BUILD_SHA=unknown
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
  sudo install -m 640 -o root -g cskang "$tmp_env" "$ENV_FILE"
  rm -f "$tmp_env"
  echo "Created $ENV_FILE"
fi

sudo install -m 644 -o root -g root deploy/production/gunicorn_thedetect.service /etc/systemd/system/gunicorn_thedetect.service
sudo install -m 644 -o root -g root deploy/production/cloudflared_detect.service /etc/systemd/system/cloudflared_detect.service
sudo install -m 644 -o root -g root deploy/production/nginx_thedetect.conf /etc/nginx/sites-available/thedetect
sudo ln -sfn /etc/nginx/sites-available/thedetect /etc/nginx/sites-enabled/thedetect

sudo ln -sfn "$ROOT_DIR/staticfiles" /var/www/thedetect/static
sudo ln -sfn "$ROOT_DIR/project_data" /var/www/thedetect/media

export PUBLIC_DOMAIN CLOUDFLARED_TUNNEL_NAME CLOUDFLARED_TUNNEL_CRED_FILE CLOUDFLARED_TUNNEL_CONFIG CLOUDFLARED_ORIGIN_CERT
sudo -E python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess

public_domain = os.environ["PUBLIC_DOMAIN"]
tunnel_name = os.environ["CLOUDFLARED_TUNNEL_NAME"]
credentials_file = os.environ["CLOUDFLARED_TUNNEL_CRED_FILE"]
config_path = Path(os.environ["CLOUDFLARED_TUNNEL_CONFIG"])
origin_cert = os.environ["CLOUDFLARED_ORIGIN_CERT"]
tmp_config_path = Path("/tmp/cloudflared_detect.yml")


def run_cloudflared(*args: str) -> str:
    completed = subprocess.run(
        [
            "sudo",
            "cloudflared",
            "--origincert",
            origin_cert,
            "--loglevel",
            "error",
            "tunnel",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


existing = json.loads(run_cloudflared("list", "-o", "json", "-n", tunnel_name))
if existing:
    tunnel_id = existing[0]["id"]
else:
    created = json.loads(
        run_cloudflared(
            "create",
            "-o",
            "json",
            "--credentials-file",
            credentials_file,
            tunnel_name,
        )
    )
    tunnel_id = created["id"]

tmp_config_path.write_text(
    "\n".join(
        [
            f"tunnel: {tunnel_id}",
            f"credentials-file: {credentials_file}",
            "ingress:",
            f"  - hostname: {public_domain}",
            "    service: http://127.0.0.1:80",
            "    originRequest:",
            f"      httpHostHeader: {public_domain}",
            "  - service: http_status:404",
            "",
        ]
    )
)
subprocess.run(
    [
        "sudo",
        "install",
        "-m",
        "644",
        "-o",
        "root",
        "-g",
        "root",
        str(tmp_config_path),
        str(config_path),
    ],
    check=True,
)
tmp_config_path.unlink(missing_ok=True)
run_cloudflared("route", "dns", "--overwrite-dns", tunnel_id, public_domain)
PY

set -a
. "$ENV_FILE"
set +a
export DJANGO_SETTINGS_MODULE=theDetect.settings

if [ -f requirements.txt ] && [ "${SKIP_PIP_INSTALL:-0}" != "1" ]; then
  "$PYTHON_BIN" -m pip install -r requirements.txt
fi
"$PYTHON_BIN" manage.py collectstatic --noinput
"$PYTHON_BIN" manage.py migrate --noinput
"$PYTHON_BIN" manage.py check --deploy
sudo chown -R cskang:www-data "$ROOT_DIR/staticfiles" "$ROOT_DIR/project_data"
sudo chmod -R u+rwX,g+rwX "$ROOT_DIR/staticfiles" "$ROOT_DIR/project_data"

sudo systemctl daemon-reload
sudo rm -f /run/gunicorn_thedetect.sock
sudo systemctl enable gunicorn_thedetect.service
sudo systemctl restart gunicorn_thedetect.service
sudo systemctl enable cloudflared_detect.service
sudo systemctl restart cloudflared_detect.service
sudo nginx -t
sudo systemctl restart nginx

echo "theDetect production deployment files installed."
