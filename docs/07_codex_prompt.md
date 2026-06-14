# theDetect 전체 구현용 Codex Master Prompt

너는 `theDetect` 서비스를 구현하는 시니어 풀스택 개발자다.

theDetect는 Android 스마트폰 카메라 기반 모바일 객체탐지 앱과 Django 서버 기반 객체탐지 학습·배포 콘솔로 구성된다.

## 1. 기본 정보

```text
Service name: theDetect
Android app: Kotlin + Jetpack Compose
Minimum Android OS: Android 11
Camera: CameraX
Server: Python Django 5.2
Database: sqlite3
Python virtual environment: dj5
Django project name: theDetect
Django root directory: /home/cskang/ganzskang/theDetect
Docs directory: ./docs
Service URL: https://detect.thesysm.com
```

## 2. 핵심 구현 목표

- Object Classes 관리
- 이미지 다중 업로드 / ZIP 업로드
- 서버 웹 Bounding Box 라벨링
- DB에는 원본 이미지 기준 픽셀 좌표 저장
- Dataset Build 시 YOLO 형식으로 변환
- Ultralytics YOLO 학습
- 학습 모델을 Android용 `.tflite`로 변환
- `model.tflite`, `labels.txt`, `metadata.json` 생성
- Android 앱에서 기본 모델 내장 및 서버 최신 모델 다운로드
- Android 앱에서 Server Mode와 On-device Mode 지원
- 양쪽 탐지 결과 모두 DetectionLog 저장
- JWT 인증
- MVP 자동 로그인

## 3. 서버 UI

```text
Django Template
HTMX
Alpine.js
Tailwind CSS
```

Tailwind 기반 SaaS 관리자 콘솔 스타일로 구현한다.

## 4. Android UI

```text
Kotlin
Jetpack Compose
Material 3
CameraX
Retrofit
OkHttp
TensorFlow Lite
```

Light/Dark Theme를 지원하고, 카메라 탐지 화면은 다크 스타일 우선으로 구현한다.

## 5. 초기 클래스

```text
class_01
class_02
other
```

## 6. 반드시 지킬 원칙

- 기존 기능 삭제 금지
- 각 단계마다 smoke test 가능한 상태 유지
- 마이그레이션 누락 금지
- settings.py 변경 시 이유 기록
- 보안 정보 하드코딩 금지
- ZIP path traversal 방어
- 업로드 파일 확장자/크기 검증
- 학습/변환 작업은 background 실행
- 향후 Celery + Redis로 전환 가능한 구조
- Android 네트워크 오류/인증 오류/모델 다운로드 실패 fallback 구현
- On-device Mode는 Ultralytics YOLO TFLite 후처리 구조 기준

## 7. 완료 후 문서화
다음 문서를 반드시 업데이트한다.

```text
./docs/implementation_result.md
./docs/server_test_checklist.md
./docs/android_test_checklist.md
./docs/known_issues.md
./docs/next_steps.md
```
