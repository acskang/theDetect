# MDetect 모델 학습 파이프라인 설계서

## 1. 전체 흐름

```text
ObjectClass 등록
→ 이미지 업로드
→ Bounding Box 라벨링
→ Dataset Build
→ YOLO 학습
→ best.pt 생성
→ Android Model Export
→ model.tflite + labels.txt + metadata.json 생성
→ Model Deployment
```

## 2. 라벨 좌표
DB에는 원본 이미지 기준 픽셀 좌표를 저장한다.

```text
x_min, y_min, x_max, y_max, image_width, image_height
```

Dataset Build 시 YOLO 정규화 좌표로 변환한다.

```text
class_id x_center y_center width height
```

변환 공식:

```text
x_center = ((x_min + x_max) / 2) / image_width
y_center = ((y_min + y_max) / 2) / image_height
width = (x_max - x_min) / image_width
height = (y_max - y_min) / image_height
```

## 3. Dataset Build 옵션

```text
dataset version name
train ratio
val ratio
test ratio
random seed
include only labeled images
exclude invalid boxes
build memo
```

기본값:

```text
train 80
val 10
test 10
random seed 42
```

## 4. Class Balance Warning
Dataset Build 전 다음을 경고한다.

- 특정 클래스 라벨 수 부족
- other 클래스 과다
- train/val/test split 내 클래스 누락
- invalid box 존재
- 라벨링되지 않은 이미지 과다

## 5. YOLO Dataset 구조

```text
project_data/datasets/<dataset_version>/
├── images/train/
├── images/val/
├── images/test/
├── labels/train/
├── labels/val/
├── labels/test/
└── data.yaml
```

## 6. 학습 기본값
관리자 화면에서 변경 가능하며 기본값은 다음과 같다.

```text
base model: yolo11n.pt 또는 yolov8n.pt
imgsz: 640
epochs: 50
batch: 16
device: auto
patience: 20
workers: auto
```

## 7. 학습 산출물

```text
best.pt
last.pt
results.csv
confusion_matrix.png
PR_curve.png
F1_curve.png
labels.jpg
training_config.json
metrics.json
training_log.txt
```

## 8. Android Model Export
학습 완료 모델 `best.pt`를 Android 패키지로 변환한다.

```text
model.tflite
labels.txt
metadata.json
```

`metadata.json` 포함 정보:

```text
model_version
model_format
task
input_size
classes
confidence_threshold
iou_threshold
created_at
training_job_id
dataset_version_id
metrics
```
