# MDetect Android Test Checklist

## Build
- [x] `cd mobile/MDetect && ./gradlew assembleDebug`
- [x] APK generated at `app/build/outputs/apk/debug/app-debug.apk`

## Compile Coverage
- [x] MainActivity
- [x] Compose screens
- [x] CameraX Preview and ImageAnalysis
- [x] Retrofit API client
- [x] DataStore settings/token persistence
- [x] Model Update client
- [x] On-device detector scaffold

## Manual Device Checks
- [ ] Run server with `python manage.py runserver 0.0.0.0:8000`.
- [ ] Confirm `step10_yolov8n_smoke_model` is active with `python manage.py list_trained_models`.
- [ ] Confirm PC LAN IP with `hostname -I`.
- [ ] Confirm firewall allows TCP port `8000`.
- [ ] Install debug APK.
- [ ] Grant camera permission.
- [ ] Set Server URL to `http://<PC_LAN_IP>:8000`.
- [ ] Tap Settings > Test and confirm connected.
- [ ] Tap Settings > Login and confirm authenticated.
- [ ] Set Detection Mode to `SERVER`.
- [ ] Confirm CameraX preview appears.
- [ ] Start Server Mode and point the camera at person/bus/bottle/cup/chair/laptop.
- [ ] Confirm status panel shows latency, object count, and server message.
- [ ] Confirm bounding boxes appear when objects are detected.
- [ ] Confirm `/api/detection-logs/` shows a recent `server` log.
- [ ] Switch to On-device Mode and verify model-missing fallback or loaded model status.

## Known Manual Requirement
No physical device was controlled by Codex. Device-level CameraX, LAN, permission, and overlay behavior must be verified manually by the user.
