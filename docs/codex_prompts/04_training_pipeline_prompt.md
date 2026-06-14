# Codex Prompt 04 - Training Pipeline

## 목표
Dataset Build와 Ultralytics YOLO 학습 기능을 구현한다.

## 구현
- Dataset Build 화면
- train/val/test 비율 입력, 기본 80/10/10
- DB 픽셀 좌표를 YOLO 정규화 좌표로 변환
- data.yaml 생성
- class balance warning
- TrainingJob 생성/실행
- background thread 또는 subprocess 실행

## 기본 학습값
```text
model: yolo11n.pt 또는 yolov8n.pt
imgsz: 640
epochs: 50
batch: 16
device: auto
patience: 20
```

## 산출물
best.pt, last.pt, results.csv, confusion_matrix.png, PR_curve.png, F1_curve.png, metrics.json, training_log.txt

## 완료 조건
- Dataset Build 성공
- YOLO 학습 실행
- TrainingJob 상태 표시
- TrainedModel 등록
