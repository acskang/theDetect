# MDetect 서버 설계서

## 1. 서버 역할
MDetect 서버는 객체탐지 모델의 데이터셋 관리, 라벨링, 학습, Android 모델 변환, 모델 배포, 탐지 로그 저장을 담당한다.

## 2. 권장 Django 앱 구성

```text
accounts          # JWT 인증, 테스트 계정 자동 로그인 지원
core              # Dashboard, Project Settings, 공통 레이아웃
datasets          # ObjectClass, UploadedImage, DatasetVersion
labeling          # Bounding Box 라벨링
training          # Dataset Build, TrainingJob, YOLO 학습
models_registry   # TrainedModel 관리
deployment        # Android Model Export, Model Deployment
detection         # Detection API, DetectionLog, Review Queue
api               # REST API 라우팅
```

## 3. 주요 DB 모델

### ObjectClass
```text
name
display_name
description
color
is_active
sort_order
created_at
updated_at
```

초기 seed:
```text
class_01
class_02
other
```

### UploadedImage
```text
file
original_filename
width
height
file_size
upload_source
hint_class
status
uploaded_by
created_at
updated_at
```

상태값:
```text
uploaded
labeling
labeled
invalid
excluded
```

### LabelBox
DB에는 원본 이미지 기준 픽셀 좌표로 저장한다.

```text
image
object_class
x_min
y_min
x_max
y_max
image_width
image_height
review_status
created_by
created_at
updated_at
```

### DatasetVersion
```text
name
description
train_ratio
val_ratio
test_ratio
random_seed
class_summary_json
build_config_json
output_path
status
created_by
created_at
```

### TrainingJob
```text
name
dataset_version
base_model
imgsz
epochs
batch
device
patience
workers
status
started_at
finished_at
log_file
artifacts_path
metrics_json
error_message
created_by
created_at
```

상태:
```text
pending
running
completed
failed
canceled
```

### TrainedModel
```text
name
training_job
model_path
class_names_json
metrics_json
is_active_server_model
created_at
```

### AndroidModelPackage
```text
name
trained_model
model_version
tflite_file
labels_file
metadata_file
input_size
confidence_threshold
iou_threshold
is_deployed
created_at
deployed_at
```

### DetectionLog
```text
mode                  # server / on_device
model_version
image
thumbnail
detections_json
top_class
top_confidence
processing_time_ms
device_info
app_version
user
review_status         # unknown / correct / wrong / ignored
actual_class
created_at
```

## 4. 서버 웹 메뉴

```text
Dashboard
Project Settings
Object Classes
Image Dataset
Labeling Workspace
Dataset Build
Training Jobs
Model Registry
Android Model Export
Model Deployment
Detection Logs
Review Queue
API Test
```

## 5. 이미지 업로드
다중 이미지 업로드와 ZIP 업로드를 모두 지원한다.

지원 확장자:
```text
jpg, jpeg, png, webp
```

ZIP 업로드 시 path traversal 공격을 방지해야 한다.

권장 ZIP 구조:
```text
dataset_upload.zip
├── class_01/
├── class_02/
└── other/
```

폴더명은 초기 힌트일 뿐이고, 실제 학습 라벨은 LabelBox 기준이다.

## 6. 작업 실행 방식
MVP에서는 background thread 또는 subprocess로 학습/변환 작업을 실행한다. 향후 Celery + Redis로 확장할 수 있도록 실행 로직을 분리한다.

## 7. 파일 저장 구조

```text
project_data/
├── uploads/
├── datasets/
├── training_runs/
├── trained_models/
├── android_exports/
└── detection_logs/
```
