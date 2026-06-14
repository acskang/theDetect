# MDetect 서비스 개요 설계서

## 1. 목적
MDetect는 Android 스마트폰 카메라로 물체를 보면서, 서버에서 학습·배포한 객체탐지 모델을 이용해 객체를 실시간 또는 준실시간으로 탐지하는 모바일 객체탐지 학습·배포 플랫폼 MVP이다.

초기 MVP는 특정 물체 전용이 아니라 `class_01`, `class_02`, `other`로 시작하고, 이후 관리자가 클래스를 추가할 수 있는 범용 구조로 설계한다.

## 2. 확정 조건

| 항목 | 내용 |
|---|---|
| 모바일 앱명 | MDetect |
| Android 개발 | Kotlin, Jetpack Compose |
| Android OS | Android 11 이상 |
| 카메라 | CameraX |
| 탐지 방식 | Server Mode + On-device Mode 둘 다 구현 |
| 서버 | Python Django 5.2 |
| DB | sqlite3 |
| Python 가상환경 | dj5 |
| Django Project | theDetect |
| Root Directory | `/home/cskang/ganzskang/theDetect` |
| 문서 위치 | `./docs` |
| 서비스 URL | `https://detect.thesysm.com` |
| 서버 UI | Django Template + HTMX + Alpine.js + Tailwind CSS |
| 서버 UI 스타일 | Tailwind 기반 SaaS 관리자 콘솔 |
| 학습 프레임워크 | Ultralytics YOLO |
| Android 모델 | `.tflite` + `labels.txt` + `metadata.json` |
| API 인증 | JWT |
| MVP 로그인 | 고정 테스트 계정 자동 로그인 |

## 3. 핵심 서비스 흐름

```text
Object Classes 등록
→ 이미지 업로드 / ZIP 업로드
→ 서버 웹에서 Bounding Box 라벨링
→ Dataset Build
→ YOLO 학습
→ best.pt 생성
→ Android Model Export
→ model.tflite + labels.txt + metadata.json 생성
→ Model Deployment
→ Android 앱에서 최신 모델 다운로드
→ CameraX 기반 탐지
→ DetectionLog 서버 저장
→ Review Queue 검수
→ 재학습 데이터로 편입
```

## 4. 탐지 모드

### Server Mode
Android 앱이 카메라 프레임을 설정된 주기마다 서버로 전송하고, Django 서버가 active YOLO 모델로 탐지한 뒤 결과를 반환한다.

기본 전송 주기: 1초에 1장  
설정 가능 값: 0.5초, 1초, 2초

전송 이미지 최적화:

```text
긴 변 1280px 이하 리사이즈
JPEG quality 80
multipart/form-data 전송
```

### On-device Mode
Android 앱 내부의 TFLite 모델로 스마트폰에서 직접 탐지한다. Ultralytics YOLO Android 예제 구조를 기준으로 TFLite 로딩, YOLO 후처리, NMS, 좌표 변환, Overlay 표시를 구현한다.

## 5. 모델 배포 정책
앱에는 기본 샘플 모델을 내장하고, 서버에 최신 모델이 있으면 다운로드해서 교체한다.

```text
assets/mdetect_default.tflite
assets/labels.txt
assets/metadata.json
```

서버 배포 패키지:

```text
model.tflite
labels.txt
metadata.json
```

## 6. 초기 클래스

```text
class_01
class_02
other
```

`other`는 대상이 아닌 물체를 잘못 탐지하는 것을 줄이기 위한 오탐 방지 클래스이다.
