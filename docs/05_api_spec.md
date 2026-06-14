# theDetect API 설계서

## 1. 인증
JWT 기반 인증을 사용한다.

```http
Authorization: Bearer <access_token>
```

## 2. Auth API

### 로그인
```http
POST /api/auth/login/
```

요청:
```json
{"username":"test","password":"password"}
```

응답:
```json
{"access":"...","refresh":"..."}
```

### 토큰 갱신
```http
POST /api/auth/refresh/
```

## 3. Health Check

```http
GET /api/health/
```

응답:
```json
{"status":"ok","service":"theDetect"}
```

## 4. Server Mode Detection API

```http
POST /api/detect/server/
Content-Type: multipart/form-data
Authorization: Bearer <access_token>
```

요청 필드:

```text
image
client_timestamp
app_version
device_info
```

응답:
```json
{
  "mode": "server",
  "model_version": "mdetect_yolo_20260611_001",
  "processing_time_ms": 423,
  "image_width": 1280,
  "image_height": 720,
  "detections": [
    {
      "class_id": 0,
      "class_name": "class_01",
      "confidence": 0.87,
      "box": {"x_min":120,"y_min":80,"x_max":420,"y_max":500}
    }
  ],
  "log_id": 123
}
```

## 5. On-device Log API

```http
POST /api/detect/on-device-log/
Authorization: Bearer <access_token>
```

요청:
```json
{
  "model_version": "mdetect_yolo_20260611_001",
  "app_version": "1.0.0",
  "device_info": "Galaxy S21 / Android 11",
  "processing_time_ms": 35,
  "detections": [
    {
      "class_id": 1,
      "class_name": "class_02",
      "confidence": 0.91,
      "box": {"x_min":100,"y_min":120,"x_max":480,"y_max":620}
    }
  ]
}
```

## 6. Detection History API

```http
GET /api/detection-logs/?limit=20
Authorization: Bearer <access_token>
```

## 7. Android Model API

### 최신 모델 정보
```http
GET /api/models/android/latest/
Authorization: Bearer <access_token>
```

응답:
```json
{
  "model_version": "mdetect_yolo_20260611_001",
  "input_size": 640,
  "classes": ["class_01", "class_02", "other"],
  "confidence_threshold": 0.5,
  "iou_threshold": 0.45,
  "files": {
    "model_tflite": "/api/models/android/latest/model.tflite",
    "labels": "/api/models/android/latest/labels.txt",
    "metadata": "/api/models/android/latest/metadata.json"
  }
}
```

### 파일 다운로드
```http
GET /api/models/android/latest/model.tflite
GET /api/models/android/latest/labels.txt
GET /api/models/android/latest/metadata.json
```
