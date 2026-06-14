# MDetect Android Model Export Manual

## Export Package
1. Train a YOLO model and confirm a `TrainedModel` exists in Model Registry.
2. Open `/models/android/export/`.
3. Select the TrainedModel.
4. Enter `model_version`.
5. Confirm defaults:
   - input size: `640`
   - confidence threshold: `0.5`
   - IoU threshold: `0.45`
6. Start export.

The export runner writes:

```text
model.tflite
labels.txt
metadata.json
export_log.txt
```

## labels.txt
Labels are generated from `TrainedModel.class_names_json`, preserving the Dataset Build class ID order.

Example:

```text
class_01
class_02
other
```

## metadata.json
Example:

```json
{
  "model_version": "mdetect_yolo_20260611_001",
  "model_format": "tflite",
  "task": "object_detection",
  "input_size": 640,
  "classes": ["class_01", "class_02", "other"],
  "confidence_threshold": 0.5,
  "iou_threshold": 0.45,
  "training_job_id": 1,
  "dataset_version_id": 1,
  "trained_model_id": 1,
  "metrics": {}
}
```

## Deploy Package
Open the package detail page and click Set deployed. Only one Android package can be deployed at a time.
