# MDetect Android Model API Guide

All Android model APIs require JWT authentication.

## Latest Model Info
```bash
curl https://detect.thesysm.com/api/models/android/latest/ \
  -H "Authorization: Bearer <access-token>"
```

Response includes:

```json
{
  "model_version": "mdetect_yolo_20260611_001",
  "input_size": 640,
  "classes": ["class_01", "class_02", "other"],
  "confidence_threshold": 0.5,
  "iou_threshold": 0.45,
  "files": {
    "model_tflite": "https://detect.thesysm.com/api/models/android/latest/model.tflite",
    "labels": "https://detect.thesysm.com/api/models/android/latest/labels.txt",
    "metadata": "https://detect.thesysm.com/api/models/android/latest/metadata.json"
  }
}
```

## Downloads
```bash
curl https://detect.thesysm.com/api/models/android/latest/model.tflite \
  -H "Authorization: Bearer <access-token>" -o model.tflite

curl https://detect.thesysm.com/api/models/android/latest/labels.txt \
  -H "Authorization: Bearer <access-token>" -o labels.txt

curl https://detect.thesysm.com/api/models/android/latest/metadata.json \
  -H "Authorization: Bearer <access-token>" -o metadata.json
```

## No Deployed Model
If no completed package is deployed, the latest model API returns HTTP 404 with a JSON error.

## Next Step
Step 06 Android app implementation will use these endpoints to check for the latest model and download the three package files.
