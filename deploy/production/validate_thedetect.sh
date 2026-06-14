#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="/etc/thedetect/thedetect.env"
PYTHON_BIN="${PYTHON_BIN:-/home/cskang/miniconda3/envs/dj5/bin/python}"
PUBLIC_DOMAIN="${THEDETECT_PUBLIC_DOMAIN:-detect.thesysm.com}"

cd "$ROOT_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

sudo -v

set -a
. "$ENV_FILE"
set +a
export DJANGO_SETTINGS_MODULE=theDetect.settings

"$PYTHON_BIN" manage.py check
curl --silent --show-error --fail --unix-socket /run/gunicorn_thedetect.sock -H "Host: ${PUBLIC_DOMAIN}" -H 'X-Forwarded-Proto: https' http://localhost/healthz/
curl --silent --show-error --fail --unix-socket /run/gunicorn_thedetect.sock -H "Host: ${PUBLIC_DOMAIN}" -H 'X-Forwarded-Proto: https' http://localhost/readyz/
if ! curl --silent --show-error --fail --max-time 20 "https://${PUBLIC_DOMAIN}/healthz/" >/dev/null; then
  resolved_ip="$(
    nslookup -type=A "$PUBLIC_DOMAIN" 1.1.1.1 \
      | awk '/^Address: / && $2 !~ /#/ && $2 ~ /^[0-9.]+$/ {print $2}' \
      | head -n 1
  )"
  if [ -z "$resolved_ip" ]; then
    echo "Could not resolve ${PUBLIC_DOMAIN} via local resolver or 1.1.1.1" >&2
    exit 1
  fi
  curl --silent --show-error --fail --max-time 20 --resolve "${PUBLIC_DOMAIN}:443:${resolved_ip}" "https://${PUBLIC_DOMAIN}/healthz/" >/dev/null
fi
sudo systemctl status gunicorn_thedetect.service --no-pager --lines=0
sudo systemctl status nginx --no-pager --lines=0
sudo systemctl status cloudflared_detect.service --no-pager --lines=0
