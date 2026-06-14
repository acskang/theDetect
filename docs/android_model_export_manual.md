# MDetect Android Model Export Manual

## Export Python Environment
The Django server can keep running in the `dj5` environment, but TFLite export should use the Python 3.11 export environment:

```text
/home/cskang/miniconda3/envs/mdetect-export/bin/yolo
```

The server setting is:

```text
MDETECT_EXPORT_YOLO_BIN=/home/cskang/miniconda3/envs/mdetect-export/bin/yolo
```

Check it from the project root:

```bash
python manage.py shell -c "from deployment.exporter import yolo_executable; print(yolo_executable())"
```

Expected:

```text
/home/cskang/miniconda3/envs/mdetect-export/bin/yolo
```

This avoids the Python 3.13 `dj5` TensorFlow wheel issue during `format=tflite` export.

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
