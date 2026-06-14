# MDetect Android App Result

## Project Location
```text
mobile/MDetect
```

## Package
```text
com.thesysm.mdetect
```

## Implemented Screens
- Splash
- Home
- Camera Detection
- Detection History
- Model Update
- Settings

## Implemented App Structure
- Jetpack Compose UI
- Material 3 light/dark theme
- CameraX Preview and ImageAnalysis
- Runtime camera permission request
- Retrofit + OkHttp API client
- DataStore settings/token storage
- JWT auto-login and token persistence
- Server URL editing
- Server Mode client and fallback status handling
- Android model latest check and file download flow
- On-device TFLite loading and safe fallback structure
- Detection overlay drawing

## Build
```bash
cd mobile/MDetect
./gradlew assembleDebug
```

Output:

```text
app/build/outputs/apk/debug/app-debug.apk
```

## Known Limitations
- Server detection requires an active Django `TrainedModel` with a valid local YOLO `.pt` file. Without one, Server Mode displays the server `model_available=false` message.
- On-device YOLO post-processing is scaffolded with safe fallback; full output-shape-specific decoding should be completed after validating the exported TFLite model.
- Detection history uses the server's minimal history API and has limited filtering/detail support.
