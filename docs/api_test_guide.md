# MDetect API Test Guide

## Health Check
```bash
curl http://127.0.0.1:8000/api/health/
```

## Create MVP Test User
```bash
MDETECT_TEST_USERNAME=test MDETECT_TEST_PASSWORD='<password>' python manage.py ensure_mvp_test_user
```

## JWT Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"<password>"}'
```

## JWT Refresh
```bash
curl -X POST http://127.0.0.1:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh-token>"}'
```

## Protected Test
```bash
curl http://127.0.0.1:8000/api/auth/protected-test/ \
  -H "Authorization: Bearer <access-token>"
```

## Server Detection
No active server model:

```bash
curl -X POST http://127.0.0.1:8000/api/detect/server/ \
  -H "Authorization: Bearer <access-token>" \
  -F "image=@frame.jpg"
```

Expected behavior: HTTP 200 with `model_available=false` and an empty `detections` list.

With an active `TrainedModel` whose `model_path` points to a valid YOLO `.pt` file, the same request returns `model_available=true`, detection boxes, and a `DetectionLog` id.

Invalid upload examples:

```bash
curl -X POST http://127.0.0.1:8000/api/detect/server/ \
  -H "Authorization: Bearer <access-token>"
```

Expected behavior: HTTP 400 with `message="image is required."`.

## Detection Logs
```bash
curl http://127.0.0.1:8000/api/detection-logs/?limit=20 \
  -H "Authorization: Bearer <access-token>"
```
