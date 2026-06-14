# theDetect

theDetect is a Django-based object detection console with an Android client prototype.

## Contents

- Django server apps for dataset upload, labeling, dataset build, training, model registry, deployment, and detection APIs.
- Android app prototype under `mobile/MDetect`.
- Project design notes, manuals, implementation logs, and next steps under `docs/`.

## Notes

Runtime data and generated artifacts are intentionally excluded from git:

- `db.sqlite3`
- `project_data/`
- `staticfiles/`
- model weights such as `*.pt`, `*.onnx`, and `*.tflite`
- Android build output and local machine settings

See `docs/README.md` and `docs/implementation_result.md` for the current implementation history.

