# MDetect Android Real Device Test Guide

## Django Server
Start from the repository root:

```bash
cd /home/cskang/ganzskang/theDetect
source activate dj5
```

If your shell uses Conda differently, activate the existing `dj5` environment with the local equivalent command.

Create or confirm the MVP user:

```bash
MDETECT_TEST_USERNAME=mdetect_smoke MDETECT_TEST_PASSWORD=local-smoke-password python manage.py ensure_mvp_test_user
```

Confirm the active smoke model:

```bash
python manage.py list_trained_models
```

Expected active line:

```text
* id=4 name=step10_yolov8n_smoke_model ... usable_pt=True
```

If it is not active:

```bash
python manage.py set_active_model --id <step10_yolov8n_smoke_model_id>
```

Run the Django server on a LAN-visible address:

```bash
python manage.py runserver 0.0.0.0:8000
```

## PC LAN IP
Find the PC LAN IP:

```bash
hostname -I
```

or:

```bash
ip addr
```

Use the LAN IP, not `127.0.0.1`, on a real phone.

## Firewall
Check firewall status:

```bash
sudo ufw status
```

If needed, allow port 8000:

```bash
sudo ufw allow 8000/tcp
```

Do not run firewall commands unless you understand the host security impact.

## Android Settings
On the phone, set Server URL to:

```text
http://<server-lan-ip>:8000
```

Example:

```text
http://192.168.0.25:8000
```

Rules:
- Android Emulator uses `http://10.0.2.2:8000`.
- Real smartphones use the PC LAN IP.
- The phone and server must be on the same Wi-Fi/LAN.
- The firewall must allow inbound TCP port `8000`.
- If needed, include the LAN IP in `DJANGO_ALLOWED_HOSTS`.

In the app:
1. Open `MDetect`.
2. Go to `Settings`.
3. Set `Server URL` to `http://<PC_LAN_IP>:8000`.
4. Tap `Save`.
5. Tap `Test` and confirm `Server test: Connected`.
6. Tap `Login` and confirm authenticated status.
7. Set `Detection Mode` to `SERVER`.
8. Use `1.0s` Server Mode interval for the first test.

## Checks
- Settings > Test should report connected when `/api/health/` is reachable.
- Settings > Login should authenticate with JWT.
- Model Update should download `model.tflite`, `labels.txt`, and `metadata.json` when a package is deployed.
- Camera Detection should show live preview after permission is granted.
- Camera Detection in Server Mode should show detections when a valid active model exists.
- If no active server model exists, Camera Detection should show `No active server model is available.` without crashing.
- After Server Mode frames are sent, confirm `/api/detection-logs/` shows a recent `server` log.
- The Camera status panel should show `Server: ok model_available=true log_id=<id>` on successful server inference.

## Server Mode curl Check
Before testing on the phone, verify the same server with curl:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"mdetect_smoke","password":"local-smoke-password"}' | python -c "import sys,json; print(json.load(sys.stdin)['access'])")

curl -X POST http://127.0.0.1:8000/api/detect/server/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/test.jpg" \
  -F "device_info=curl-smoke" \
  -F "app_version=server-test"
```

Check `model_available`, `model_version`, `detections`, `processing_time_ms`, and `log_id`.

Minimum success criteria:

```text
model_available=true
message=ok
log_id=<number>
```

`detections` may be empty if the image does not contain a recognizable object. Use a known object image for stronger validation.

## Final Server Mode Checklist
1. Server runs with `python manage.py runserver 0.0.0.0:8000`.
2. PC LAN IP is confirmed with `hostname -I`.
3. Phone and PC are on the same Wi-Fi/LAN.
4. Android Settings server URL is `http://<PC_LAN_IP>:8000`.
5. Settings > Test reports connected.
6. Settings > Login authenticates.
7. Camera Detection opens.
8. Detection Mode is `SERVER`.
9. Start detection.
10. Point the camera at common COCO objects such as a person, bus, bottle, cup, chair, or laptop.
11. Status panel shows latency, object count, and server message.
12. Bounding boxes appear when YOLO detects an object.
13. Server `/api/detection-logs/` shows a recent log.

The active smoke model is pretrained YOLOv8n COCO. Seeing `person`, `bus`, `bottle`, or `cup` is correct. The project-specific `class_01/class_02/other` model must be trained and activated later.

## DetectionLog Check
From the server PC:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"mdetect_smoke","password":"local-smoke-password"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access'])")

curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/api/detection-logs/
```

Confirm the newest item has:
- `mode=server`
- `model_version=step10_yolov8n_smoke_model`
- `top_class` when detections exist
- a recent `created_at`

## APK
Build:

```bash
cd mobile/MDetect
./gradlew assembleDebug
```

APK:

```text
mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk
```

Install with adb if a device is connected and USB debugging is enabled:

```bash
adb install -r mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk
```

If `adb` is not available, install manually:
1. Copy `app-debug.apk` to the phone.
2. Open it from a file manager.
3. Allow installing unknown apps when prompted.
4. Install.
5. Launch MDetect and allow camera permission.

## Failure Checklist
- `Settings > Test` fails: verify phone and PC are on the same network, server is running on `0.0.0.0:8000`, firewall allows `8000/tcp`, and the app URL uses the PC LAN IP.
- Login fails: rerun `ensure_mvp_test_user` and check username/password in Settings.
- Camera opens but no boxes: point at common COCO objects and check whether status says `model_available=true`.
- Status shows no active model: run `python manage.py list_trained_models` and activate `step10_yolov8n_smoke_model`.
- DetectionLog does not increase: confirm the app is in `SERVER` mode and detection is started.

## Result Notes
- The Android debug APK builds successfully.
- The server provides real YOLO inference on `/api/detect/server/` when an active model is available.
- Real-device testing remains manual: install the APK, point Settings to a LAN-visible Django server, and verify camera/network/model update flows.
