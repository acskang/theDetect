## theDetect Production Deployment Assets

Target topology:

- Dedicated Cloudflare Tunnel (`detect`)
- Nginx
- Gunicorn
- Django (`theDetect.settings`)

Installed targets:

- systemd service: `/etc/systemd/system/gunicorn_thedetect.service`
- systemd service: `/etc/systemd/system/cloudflared_detect.service`
- environment file: `/etc/thedetect/thedetect.env`
- nginx site: `/etc/nginx/sites-available/thedetect`
- nginx symlink: `/etc/nginx/sites-enabled/thedetect`
- cloudflared config: `/etc/cloudflared/detect.yml`
- cloudflared credentials: `/etc/cloudflared/detect-credentials.json`

Runtime paths:

- public socket path: `/run/gunicorn_thedetect.sock`
- actual socket path: `/run/thedetect/gunicorn.sock`
- static alias root: `/var/www/thedetect/static`
- media alias root: `/var/www/thedetect/media`
- application logs: `/logs/thedetect`

Production URL:

```text
https://detect.thesysm.com
```

Run:

```bash
bash deploy/production/run_thedetect_deploy.sh
```
