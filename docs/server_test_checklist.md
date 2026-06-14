# MDetect Server Test Checklist

## Commands
- [x] `python manage.py check`
- [x] `python manage.py makemigrations --check`
- [x] `python manage.py migrate`
- [x] `python manage.py test`

## Pages
- [x] `/`
- [x] `/classes/`
- [x] `/datasets/images/`
- [x] `/labeling/`
- [x] `/datasets/build/`
- [x] `/datasets/versions/`
- [x] `/training/jobs/`
- [x] `/models/registry/`
- [x] `/models/android/export/`
- [x] `/models/android/packages/`
- [x] `/api-test/`

## APIs
- [x] `GET /api/health/`
- [x] `POST /api/auth/login/`
- [x] `POST /api/auth/refresh/`
- [x] `GET /api/auth/protected-test/`
- [x] `GET /api/models/android/latest/`
- [x] `GET /api/models/android/latest/model.tflite`
- [x] `GET /api/models/android/latest/labels.txt`
- [x] `GET /api/models/android/latest/metadata.json`
- [x] `POST /api/detect/server/`
- [x] `GET /api/detection-logs/`

## Notes
- Android model APIs require a deployed `AndroidModelPackage`.
- Server Detection API is stable but returns empty detections until real server-side YOLO inference is implemented.
