# Codex Prompt 06 - Model Deployment

## 목표
학습 완료 YOLO 모델을 Android용 모델 패키지로 변환하고 배포 API를 구현한다.

## 입력
best.pt

## 출력
model.tflite, labels.txt, metadata.json

## 구현
- Android Model Export 화면
- 변환 실행/상태/로그 표시
- AndroidModelPackage 등록
- 배포 모델 지정
- 최신 모델 API
- 파일 다운로드 API

## API
GET /api/models/android/latest/
GET /api/models/android/latest/model.tflite
GET /api/models/android/latest/labels.txt
GET /api/models/android/latest/metadata.json

## 완료 조건
- tflite 변환 가능
- labels/metadata 생성
- 최신 모델 다운로드 가능
