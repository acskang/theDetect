# MDetect Integration Test Result

## Server Result
- `python manage.py check`: PASS
- `python manage.py makemigrations --check`: PASS
- `python manage.py migrate`: PASS
- `python manage.py test`: PASS, 30 tests

## Android Result
- `cd mobile/MDetect && ./gradlew assembleDebug`: PASS
- Debug APK: `mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk`

## API Endpoint Match
Android client and Django server now match:
- `GET /api/health/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/protected-test/`
- `GET /api/models/android/latest/`
- `GET /api/models/android/latest/model.tflite`
- `GET /api/models/android/latest/labels.txt`
- `GET /api/models/android/latest/metadata.json`
- `POST /api/detect/server/`
- `GET /api/detection-logs/`

## Model Update Integration
- No deployed package: API returns a clear 404 JSON error.
- Fake deployed package: latest model API returns HTTP 200.
- `model.tflite`, `labels.txt`, and `metadata.json` download APIs return HTTP 200 with JWT.
- Android Model Update client is compatible with the latest model response.

## Server Mode Current Scope
`POST /api/detect/server/` runs real YOLO inference when an active server `TrainedModel` points to a valid local model file. If no active server model exists, it returns:

```json
{
  "mode": "server",
  "model_version": null,
  "model_available": false,
  "processing_time_ms": 0,
  "image_width": 0,
  "image_height": 0,
  "detections": [],
  "message": "No active server model is available.",
  "log_id": null
}
```

When an active model is available, the endpoint returns `model_available=true`, detection boxes, timing, and a `DetectionLog` id.

## Detection History Current Scope
`GET /api/detection-logs/` returns recent logs as:

```json
{"results": []}
```

Android History screen now expects this wrapper.

## Smoke Account
Use the existing environment-driven command:

```bash
MDETECT_TEST_USERNAME=mdetect_smoke MDETECT_TEST_PASSWORD=local-smoke-password python manage.py ensure_mvp_test_user
```

The password is not hardcoded in server code.
