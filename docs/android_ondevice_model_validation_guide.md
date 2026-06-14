# Android On-device Model Validation Guide

## Purpose
Step 20 prepares real-device validation for Android On-device Mode.

Step 19 added first-pass YOLO TFLite preprocessing and decoding. Step 20 makes the actual downloaded model package easier to verify by exposing local file state, tensor shapes, decoder layout, detections count, and last error in the app and Logcat.

## Check Deployed Android Package
From the repository root:

```bash
python manage.py shell -c "from deployment.models import AndroidModelPackage; print(list(AndroidModelPackage.objects.filter(is_deployed=True).values('id','model_version','status','tflite_file','labels_file','metadata_file')))"
```

Expected:

```text
status='completed'
tflite_file is not empty
labels_file is not empty
metadata_file is not empty
```

Current local check on 2026-06-14 showed:

```text
id=2
model_version=mdetect_integration_001
status=completed
```

If no deployed package exists:

```text
Model Registry
-> Android Model Export
-> select a TrainedModel
-> Start export
-> Android Model Package detail
-> Set deployed
-> Android app Model Update
```

## Model Update Download Check
In the Android app:

1. Open `Settings`.
2. Set the server URL.
3. Tap `Test`.
4. Tap `Login`.
5. Open `Model Update`.
6. Tap `Check latest model`.
7. Confirm `Latest server model`.
8. Tap `Download model package`.
9. Confirm:

```text
Downloaded files: model=yes labels=yes metadata=yes
Local model size: > 0 bytes
Local model: <model_version>
```

The app logs model download events with:

```text
MDetectModelUpdate
```

## On-device Real-device Test
1. Start the Django server on a LAN-visible address.
2. Confirm a deployed Android model package.
3. Install the latest debug APK.
4. Configure Android Settings server URL.
5. Download the model from Model Update.
6. Set `Detection Mode` to `ON_DEVICE`.
7. Open `Camera Detection`.
8. Tap `START DETECTION`.
9. Point the camera at a trained object.
10. Check the status panel for:

```text
Model
Local files
Input
Output
Layout
Objects
Latency
Last error
```

11. Check Logcat for:

```text
MDetectOnDevice
MDetectModelUpdate
MDetectCamera
```

## Logcat Commands
With `adb` available:

```bash
adb logcat -s MDetectOnDevice MDetectModelUpdate MDetectCamera
```

Useful logs include:

- model path
- metadata path
- labels path
- input tensor shape and dtype
- output tensor count, shape, and dtype
- decoder layout
- inference time
- detections count
- error summary

## Shape Mismatch Data To Collect
If On-device Mode does not show boxes or reports an unsupported shape, collect:

- `model_version`
- input tensor shape
- input tensor dtype
- output tensor count
- each output tensor shape
- each output tensor dtype
- labels count
- metadata `input_size`
- decoder layout
- Camera status panel error message
- `MDetectOnDevice` Logcat lines

This information is required before safely changing the decoder in the next step.

## Success Criteria
- Model Update shows all three files downloaded.
- Camera status panel shows input/output tensor shape.
- On-device status is either `On-device ok objects=<n>` or a clear unsupported-shape/error message.
- If detections exist, the overlay draws boxes on the preview.

## Deferred
- Decoder changes for shape variants observed during real-device testing.
- On-device DetectionLog server sync.
- GPU/NNAPI delegate support.

