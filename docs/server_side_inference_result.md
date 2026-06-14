# MDetect Server-side Inference Result

## Scope
Step 08 implements real server-side YOLO inference for:

```text
POST /api/detect/server/
```

The endpoint is JWT-protected and accepts `multipart/form-data` with an `image` field.

## Active Server Model
The server uses the first `models_registry.TrainedModel` where:

```text
is_active_server_model = True
```

Use the Model Registry page to activate a trained model. The model file referenced by `model_path` must exist and be readable.

### Active Model Setup
1. Open the server web console and sign in.
2. Go to `Model Registry`.
3. Confirm the target model has a valid `model_path`, usually a YOLO `best.pt`.
4. Click `Set active`.
5. Confirm the target row shows `Active = Yes`.

The activation view updates other `TrainedModel` rows to `is_active_server_model=False`, so only one server model is active.

### CLI Checks
List registered models and file status:

```bash
python manage.py list_trained_models
```

Set the active model after validating its `.pt` file:

```bash
python manage.py set_active_model --id <trained_model_id>
```

If you intentionally need to activate a record before the file exists, use:

```bash
python manage.py set_active_model --id <trained_model_id> --allow-missing-file
```

For real inference, do not use `--allow-missing-file`; the model file must exist.

## Inference Flow
1. Validate the uploaded image extension: `jpg`, `jpeg`, `png`, `webp`.
2. Validate the image with Pillow and convert it to RGB.
3. Load the active YOLO model with Ultralytics.
4. Cache the loaded model in memory by active model id, path, and file mtime.
5. Run detection with default `conf=0.25`, `iou=0.45`, `imgsz=640` or the training job image size.
6. Convert YOLO `xyxy` boxes to Android JSON using original request-image pixel coordinates.
7. Save a `DetectionLog` where possible.

## Request Example
```bash
curl -X POST http://127.0.0.1:8000/api/detect/server/ \
  -H "Authorization: Bearer <access-token>" \
  -F "image=@frame.jpg" \
  -F "app_version=1.0.0" \
  -F "device_info=Pixel Emulator"
```

## JWT + Real File curl Test
```bash
MDETECT_TEST_USERNAME=mdetect_smoke MDETECT_TEST_PASSWORD=local-smoke-password python manage.py ensure_mvp_test_user

TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"mdetect_smoke","password":"local-smoke-password"}' | python -c "import sys,json; print(json.load(sys.stdin)['access'])")

curl -X POST http://127.0.0.1:8000/api/detect/server/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/test.jpg" \
  -F "device_info=curl-smoke" \
  -F "app_version=server-test"
```

Check these fields in the response:
- `model_available`
- `model_version`
- `detections`
- `processing_time_ms`
- `log_id`

`detections` can be an empty array if the model runs successfully but finds no matching object. The first success criterion is `model_available=true`, `message=ok`, and a non-null `log_id`.

## Management Smoke Test
Run direct server inference without starting the HTTP server:

```bash
python manage.py smoke_server_detect \
  --image /path/to/test.jpg \
  --username mdetect_smoke \
  --device-info step10-command \
  --app-version step10-smoke
```

Expected successful output:

```text
model_available=true
model_version=<active-model-name>
processing_time_ms=<number>
image_width=<number>
image_height=<number>
detections_count=<number>
log_id=<id>
message=ok
```

Step 10 smoke result:

```text
model_available=true
model_version=step10_yolov8n_smoke_model
processing_time_ms=3502
image_width=810
image_height=1080
detections_count=6
log_id=2
message=ok
```

## Success Response Example
```json
{
  "mode": "server",
  "model_version": "mdetect_yolo_001",
  "model_available": true,
  "processing_time_ms": 123,
  "image_width": 1280,
  "image_height": 720,
  "detections": [
    {
      "class_id": 0,
      "class_name": "class_01",
      "confidence": 0.87,
      "box": {
        "x_min": 120,
        "y_min": 80,
        "x_max": 420,
        "y_max": 500
      }
    }
  ],
  "message": "ok",
  "log_id": 123
}
```

## No Active Model
If no active server model exists, the endpoint returns HTTP 200 with:

```json
{
  "mode": "server",
  "model_version": null,
  "model_available": false,
  "processing_time_ms": 0,
  "image_width": 1280,
  "image_height": 720,
  "detections": [],
  "message": "No active server model is available.",
  "log_id": null
}
```

## Error Handling
- Missing image: HTTP 400 JSON.
- Invalid image: HTTP 400 JSON.
- Missing model file: HTTP 200 stable JSON with `model_available=false`.
- Ultralytics import/load/inference failure: HTTP 200 stable JSON with `model_available=false`.
- DetectionLog save failure: inference response is still returned with `log_id=null`.

## DetectionLog Verification
After a successful request:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/api/detection-logs/
```

Confirm:
- `mode` is `server`.
- `model_version` matches the active model.
- `top_class` and `top_confidence` are populated when detections exist.
- `device_info` and `app_version` are stored on the underlying `DetectionLog`.
- `detections_json` stores the full detection list.

## Current Limitations
- Real YOLO inference requires `ultralytics` and compatible model dependencies in the server environment.
- The endpoint runs inference synchronously in the request path.
- No GPU scheduling, queueing, or rate limiting is implemented yet.
- Thumbnail generation is not implemented; the original request image is saved when logging succeeds.
