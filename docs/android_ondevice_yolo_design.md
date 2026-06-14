# Android On-device YOLO TFLite Design

## Scope
Step 19 adds the first real On-device Mode path for Android:

- load `model.tflite`, `labels.txt`, and `metadata.json` from `filesDir/models/current/`
- inspect TFLite input/output tensor shapes and dtypes
- decode CameraX JPEG frames into `Bitmap`
- letterbox resize to the model input size
- run TFLite inference
- decode raw YOLO output
- apply confidence threshold and class-wise NMS
- restore bounding boxes to the original bitmap coordinate system
- render results through the existing `DetectionBox` overlay

Server Mode, model download APIs, Django server code, training, and export server logic are unchanged.

## Model Package
The Android app uses the package downloaded by Model Update:

```text
filesDir/models/current/model.tflite
filesDir/models/current/labels.txt
filesDir/models/current/metadata.json
```

`labels.txt` is preferred for class names. If it is missing, `metadata.json` `classes` is used. If both exist and differ, the detector logs a warning and includes a mismatch note in the status message.

Metadata values used by the detector:

- `model_version`
- `input_size`
- `confidence_threshold`
- `iou_threshold`
- `classes`

The active TFLite tensor shape is the final source of truth for runtime input size.

## Preprocessing
The app decodes each sampled CameraX JPEG frame to a `Bitmap`.

Preprocessing:

1. Read original bitmap width and height.
2. Compute letterbox scale:

```text
scale = min(inputSize / originalWidth, inputSize / originalHeight)
```

3. Resize the bitmap with preserved aspect ratio.
4. Draw it centered on a square black `inputSize x inputSize` bitmap.
5. Create an NHWC input buffer.

Supported input dtypes:

- `FLOAT32`: RGB values normalized to `0.0..1.0`
- `UINT8`: RGB bytes copied as `0..255`

Other input dtypes fall back with a clear status message.

## Output Decoding
Step 19 supports raw single-output YOLO tensors:

```text
[1, channels, boxes]
[1, boxes, channels]
```

Supported channel layouts:

```text
4 + num_classes
5 + num_classes
```

YOLOv8-style output without objectness uses class score directly. YOLOv5-style output with objectness uses:

```text
confidence = objectness * class_score
```

Box values are treated as center-based `x, y, w, h`. If all four box values are normalized, they are multiplied by `inputSize`.

Unsupported output count, shape, or dtype returns a fallback status instead of crashing the app.

## Coordinate Restore
Detection boxes are restored to the original bitmap coordinate system:

```text
x = (x_model - padX) / scale
y = (y_model - padY) / scale
```

Coordinates are clamped to:

```text
0 <= x <= originalWidth
0 <= y <= originalHeight
```

`DetectionBox.imageWidth` and `DetectionBox.imageHeight` are set to the original bitmap size. The existing overlay scales from those dimensions to the preview canvas.

## NMS
Step 19 uses class-wise NMS.

- IoU threshold comes from settings or metadata, default `0.45`.
- Max detections are limited to `50`.
- Tiny or invalid boxes are discarded before NMS.

## Current Limitations
- Multi-output TFLite models with built-in NMS are detected but not decoded in Step 19.
- Non-FLOAT32 output tensors are not decoded.
- Some YOLO export variants may emit a different box format; those require follow-up validation against the actual exported model.
- On-device DetectionLog sync is deferred to a later step.
- GPU, NNAPI, and delegate optimization are not included in Step 19.

