# MDetect Server Core Result

## Implemented in Step 02
- Core models: `ObjectClass`, `UploadedImage`, `DatasetVersion`, `DetectionLog`.
- Seed data: `class_01`, `class_02`, `other`.
- Web console pages: Dashboard, Object Classes, Image Dataset, API Test.
- Image upload: multi-image upload and ZIP upload.
- ZIP safety: rejects absolute paths, parent traversal, directories, and non-image files.
- JWT API: login, refresh, protected test, public health check.

## Environment Variables
Use `.env.example` as a reference. The MVP test account is created with:

```text
MDETECT_TEST_USERNAME=<username>
MDETECT_TEST_PASSWORD=<password>
python manage.py ensure_mvp_test_user
```

Passwords are not stored in code.

## Not Implemented Yet
- Bounding box labeling workspace.
- Dataset build logic.
- YOLO training.
- Android model export and deployment.
- Android app.
