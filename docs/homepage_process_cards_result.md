# Homepage Process Cards Result

Date: 2026-06-14

## Purpose

Step 27 replaces the old homepage status cards with a clearer 6-step MDetect workflow. The goal is to explain how a user moves from source images to a smartphone-ready object detection model.

## Before

The homepage showed three broad status cards:

```text
Mode / Server / App
Model / YOLO Active
Console / Dataset / Logs
```

## After

The homepage now shows six process cards:

```text
STEP 01 이미지 준비
STEP 02 B-Box 라벨링
STEP 03 데이터셋 제작
STEP 04 학습 모델 생성
STEP 05 스마트폰용 모델 생성
STEP 06 스마트폰 적용
```

## Icon Meaning

- 이미지 준비: photo frame and upload arrow
- B-Box 라벨링: dashed bounding box and handles
- 데이터셋 제작: folder and data lines
- 학습 모델 생성: AI chip and node pins
- 스마트폰용 모델 생성: smartphone and model package/download
- 스마트폰 적용: smartphone detection box and check mark

## Implementation

Icons are inline SVG inside `core/templates/core/landing.html`.

No external icon package, CDN, or image file was added. Inline SVG keeps the homepage self-contained and avoids adding frontend dependencies for a small visual change.

## Intended Message

The cards communicate the main MDetect workflow:

```text
이미지 준비 -> B-Box 라벨링 -> 데이터셋 제작 -> 학습 모델 생성 -> 스마트폰용 모델 생성 -> 스마트폰 적용
```

## Impact

This is a homepage content/UI-only change. No Django model, DB, API, Android app, Dataset Build, Training, or Model Export logic was changed.
