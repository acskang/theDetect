# MDetect UI 설계서

## 1. 서버 웹 UI
서버 웹은 Tailwind 기반 SaaS 관리자 콘솔 스타일로 구현한다.

기술:
```text
Django Template
HTMX
Alpine.js
Tailwind CSS
```

## 2. 서버 레이아웃

```text
좌측 Sidebar
상단 Header
본문 Content Area
카드형 Dashboard
테이블 / 필터 / 검색 / 상태 배지
라이트 / 다크 모드
```

## 3. 서버 메뉴

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

## 4. Labeling Workspace
핵심 기능:

- 라벨링 대상 이미지 목록
- 이미지 Canvas
- 마우스 드래그 Bounding Box 생성
- 박스 선택/수정/삭제
- 클래스 선택
- 저장
- 다음 이미지 이동
- 라벨링 완료 표시

Alpine.js 상태 예:

```text
currentImage
boxes
selectedBox
currentClass
isDrawing
startPoint
endPoint
zoom
pan
```

HTMX 사용처:

```text
이미지 목록 부분 갱신
라벨 저장
라벨 삭제
상태 변경
다음 이미지 로딩
```

## 5. Training Jobs UI
표시 정보:

```text
job name
dataset version
base model
epochs
batch
device
status badge
started_at
finished_at
elapsed time
latest log
metrics
artifacts
```

학습 중 최신 로그를 주기적으로 갱신한다.

## 6. Android 앱 UI
Android 앱은 Material 3 기반으로 구현한다.

- Light/Dark Theme 지원
- Camera Detection 화면은 다크 스타일 우선
- Bounding Box는 클래스별 색상
- 상태 패널은 반투명 카드

Camera Detection 표시 요소:

```text
CameraX Preview
Bounding Box Overlay
class name
confidence
Detection Mode
Model Version
FPS
Server Latency
Network Status
Object Count
Threshold
```
