# MDetect Android App Manual Test Guide

## Build
```bash
cd mobile/MDetect
./gradlew assembleDebug
```

## Install Debug APK
```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## Server URL
Default debug URL:

```text
http://10.0.2.2:8000
```

Use Settings to change it:
- Emulator: `http://10.0.2.2:8000`
- Real device: `http://<PC-LAN-IP>:8000`
- Release/server: `https://detect.thesysm.com`

## Auto Login
Default MVP credentials:

```text
username: mdetect_smoke
password: local-smoke-password
```

These can be edited on the Settings screen.

## Camera Test
1. Open Camera Detection.
2. Grant camera permission.
3. Confirm the CameraX preview appears.
4. Tap Start.
5. Confirm status panel remains visible and the app does not crash if server detection API is unavailable.

## Model Update Test
1. Confirm the Django server has a deployed AndroidModelPackage.
2. Open Model Update.
3. Tap Check latest model.
4. Tap Download model package.
5. Confirm local model version updates.

## On-device Mode Test
1. Open Settings.
2. Select `ON_DEVICE`.
3. Save settings.
4. Open Camera Detection.
5. Tap Start.
6. If no model exists, confirm the app shows a fallback message instead of crashing.
