# Android On-device YOLO Result

## Step 19 Summary
Android On-device Mode now runs a first-pass YOLO TFLite inference path instead of always returning an empty detection list.

Implemented:

- model package loading from `filesDir/models/current/`
- labels and metadata loading
- TFLite tensor shape and dtype inspection
- Camera JPEG to Bitmap decode in the ViewModel
- letterbox resize preprocessing
- FLOAT32 and UINT8 input buffer creation
- raw YOLO output decoding for `[1, channels, boxes]` and `[1, boxes, channels]`
- support for `4 + num_classes` and `5 + num_classes` channel layouts
- confidence threshold filtering
- class-wise NMS
- bbox restore to original bitmap coordinates
- existing Detection Overlay update through `DetectionBox`
- fallback status messages for missing model, unsupported shapes, decode failures, and inference failures

## Files
- `mobile/MDetect/app/src/main/java/com/thesysm/mdetect/inference/OnDeviceDetector.kt`
- `mobile/MDetect/app/src/main/java/com/thesysm/mdetect/MDetectViewModel.kt`

## Behavior
When On-device Mode starts, the app loads:

```text
model.tflite
labels.txt
metadata.json
```

The status panel reports model load and inference status, including tensor shape information or an actionable fallback message.

On each sampled frame:

1. CameraX provides a JPEG frame.
2. The ViewModel decodes it to a Bitmap.
3. `OnDeviceDetector.detect()` preprocesses the Bitmap and runs TFLite.
4. Detections are decoded and stored in app state.
5. The existing overlay draws boxes using original bitmap coordinates.

## Verification
`./gradlew assembleDebug` passed after implementation.

Actual object detection quality still depends on validating the exported `model.tflite` tensor shape and output semantics on a real downloaded package.

## Deferred
- On-device DetectionLog server sync.
- GPU/NNAPI delegate support.
- Unit tests for post-processing math.
- Multi-output model decoding.

## Step 20 Validation Preparation
Step 20 adds validation visibility for the real downloaded Android model package.

Added:

- Camera status panel shows On-device input shape, output shape, decoder layout, detections count, and last error.
- Model Update screen shows local model version, latest server model version, downloaded file presence, labels count, and local model size.
- Logcat tags were standardized for validation:
  - `MDetectOnDevice`
  - `MDetectModelUpdate`
  - `MDetectCamera`
- `OnDeviceDetector` logs model path, metadata path, labels path, tensor info, decoder layout, inference time, detections count, and error summaries.
- The validation guide documents the deployed package check command and the shape mismatch data needed for the next decoder hardening step.

Current local deployed package check on 2026-06-14 found:

```text
id=2
model_version=mdetect_integration_001
status=completed
```

Actual detection quality and decoder compatibility still require a real phone test with the downloaded package.
