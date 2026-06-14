# MDetect Server Mode Test Guide

## 1. Prepare the Server
Start in the project directory and activate the Python environment:

```bash
cd /home/cskang/ganzskang/theDetect
source activate dj5
```

Use the local equivalent if your shell activates Conda environments differently.

Create or update the MVP smoke user:

```bash
MDETECT_TEST_USERNAME=mdetect_smoke MDETECT_TEST_PASSWORD=local-smoke-password python manage.py ensure_mvp_test_user
```

Run the Django server for local curl tests:

```bash
python manage.py runserver 127.0.0.1:8000
```

Run the Django server for Android real-device tests:

```bash
python manage.py runserver 0.0.0.0:8000
```

Check the active smoke model before starting the phone test:

```bash
python manage.py list_trained_models
```

Expected:

```text
* id=4 name=step10_yolov8n_smoke_model ... usable_pt=True
```

## 2. Activate a Server YOLO Model
1. Open `http://127.0.0.1:8000/models/registry/`.
2. Confirm a `TrainedModel` exists.
3. Confirm `model_path` points to an existing YOLO `.pt` file.
4. Click `Set active` on the target model.
5. Confirm only that model shows `Active = Yes`.

If no model is active, `/api/detect/server/` returns `model_available=false`.

If a model is active but the file is missing, `/api/detect/server/` returns `model_available=false` with a clear missing-file message.

CLI model checks:

```bash
python manage.py list_trained_models
python manage.py set_active_model --id <trained_model_id>
```

The active model is ready for real inference only when:
- `active_count` is exactly `1`.
- `model_path` exists.
- `model_path` is a file.
- `model_path` suffix is `.pt`.
- Ultralytics can load the file.

Step 10 verified active smoke model:

```text
id=4
name=step10_yolov8n_smoke_model
model_path=/home/cskang/ganzskang/theDetect/yolov8n.pt
usable_pt=True
```

## 3. Get a JWT Token
```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"mdetect_smoke","password":"local-smoke-password"}' | python -c "import sys,json; print(json.load(sys.stdin)['access'])")
```

## 4. Real Image curl Test
```bash
curl -X POST http://127.0.0.1:8000/api/detect/server/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/test.jpg" \
  -F "device_info=curl-smoke" \
  -F "app_version=server-test"
```

Confirm:
- `model_available`
- `model_version`
- `detections`
- `processing_time_ms`
- `log_id`

Successful inference can have an empty `detections` array if the test image has no object that the model recognizes. Treat `model_available=true`, `message=ok`, and a non-null `log_id` as the minimum Server Mode success signal.

## 4.1 Management Smoke Test
```bash
python manage.py smoke_server_detect \
  --image /path/to/test.jpg \
  --username mdetect_smoke \
  --device-info step10-command \
  --app-version step10-smoke
```

Step 10 verified output with Ultralytics `bus.jpg`:

```text
model_available=true
model_version=step10_yolov8n_smoke_model
detections_count=6
log_id=2
message=ok
```

## 4.2 DetectionLog Check
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/api/detection-logs/
```

Check that the latest result contains:
- `mode=server`
- `model_version=<active model>`
- `top_class` when detections exist
- `top_confidence` when detections exist

## 5. LAN Setup for Android
Find the PC LAN IP:

```bash
hostname -I
```

or:

```bash
ip addr
```

Run the server on all interfaces:

```bash
python manage.py runserver 0.0.0.0:8000
```

On the phone, use:

```text
http://<PC_LAN_IP>:8000
```

Example:

```text
http://192.168.0.25:8000
```

Network checklist:
- Android Emulator uses `http://10.0.2.2:8000`.
- Real phones use the PC LAN IP.
- Phone and PC must be on the same Wi-Fi/LAN.
- Firewall must allow inbound TCP port `8000`.
- `DJANGO_ALLOWED_HOSTS` must allow the LAN IP or include the host being used.

Firewall commands to run manually if needed:

```bash
sudo ufw status
sudo ufw allow 8000/tcp
```

## 6. Android App Test
1. Install `mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk`.
2. Open `Settings`.
3. Set `Server URL` to the LAN URL.
4. Tap `Save`.
5. Tap `Test` and confirm `Server test: Connected`.
6. Tap `Login` and confirm authenticated status.
7. Set `Detection Mode` to `SERVER`.
8. Open `Camera`.
9. Grant camera permission.
10. Tap `Start`.
11. Confirm the status panel shows latency, object count, and `Server: ok model_available=true log_id=<id>` or a clear server message.
12. Confirm server Detection Logs show a new `server` log after frames are sent.
13. For the smoke model, point the camera at COCO objects such as person, bus, bottle, cup, chair, or laptop.

For no active model, the app should show the server message:

```text
No active server model is available.
```

The app should not crash when the server returns `model_available=false`.

## Error Cases
- Active model missing: `model_available=false`, `No active server model is available.`
- Active model file missing: `model_available=false`, missing-file message.
- Model load failure: `model_available=false`, load-failure message.
- Invalid image: HTTP 400 with validation message.
- Auth failure: HTTP 401.
- Network failure on Android: Settings/Test or Camera status panel shows unavailable/failure state.

## 7. APK
Build command:

```bash
cd mobile/MDetect
./gradlew assembleDebug
```

APK:

```text
mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk
```

Install with adb:

```bash
adb install -r mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk
```

Manual install:
1. Copy the APK to the phone.
2. Open it in a file manager.
3. Allow unknown app installation.
4. Install and grant camera permission.
