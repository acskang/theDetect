# MDetect Model Deployment Result

## Implemented in Step 05
- AndroidModelPackage model.
- Android Model Export screen: `/models/android/export/`.
- Android Model Package list: `/models/android/packages/`.
- Android Model Package detail: `/models/android/packages/<package_id>/`.
- Deploy action: `/models/android/packages/<package_id>/deploy/`.
- Latest Android model API: `/api/models/android/latest/`.
- File download APIs:
  - `/api/models/android/latest/model.tflite`
  - `/api/models/android/latest/labels.txt`
  - `/api/models/android/latest/metadata.json`

## Package Files
Each Android package is written under:

```text
project_data/android_exports/<model_version>/
├── model.tflite
├── labels.txt
├── metadata.json
└── export_log.txt
```

## Deployed Model
Only one `AndroidModelPackage` is marked `is_deployed=True` at a time. The latest model API serves that deployed package.

## Known Limitations
- Real TFLite export depends on local Ultralytics/TensorFlow export support and can fail depending on environment.
- Failed exports are recorded as `failed` with `error_message`; the server remains available.
- Android app code is not included in Step 05.
