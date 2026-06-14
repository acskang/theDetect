# MDetect Android 앱 설계서

## 1. 기술 스택

```text
Kotlin
Jetpack Compose
Android 11 이상
CameraX
Retrofit + OkHttp
JWT
DataStore 또는 EncryptedSharedPreferences
TensorFlow Lite
Material 3
```

## 2. 화면 구성

```text
Splash
Home
Camera Detection
Detection History
Model Update
Settings
```

## 3. 인증 흐름
MVP에서는 고정 테스트 계정 자동 로그인을 사용한다.

```text
Splash
→ 서버 URL 로딩
→ 자동 로그인
→ JWT access/refresh token 저장
→ Home
```

401 응답 발생 시 refresh token으로 access token을 갱신한다. 운영 전환 시 Login 화면을 추가할 수 있게 구조를 열어둔다.

## 4. 서버 주소 정책
Debug/Release 빌드 타입별 기본 서버 주소를 분리한다.

```text
debug: 개발 서버 또는 로컬 서버
release: https://detect.thesysm.com
```

Settings 화면에서 서버 주소 수정과 연결 테스트를 지원한다.

## 5. Camera Detection 화면

표시 요소:

```text
CameraX Preview
Bounding Box Overlay
class name
confidence
class별 색상
Detection Mode
Model Version
FPS
Server Latency
Network Status
Object Count
Threshold
```

## 6. Server Mode

```text
CameraX ImageAnalysis
→ 프레임 획득
→ Bitmap 변환
→ 회전 보정
→ 긴 변 1280px 이하 리사이즈
→ JPEG quality 80 압축
→ multipart/form-data 전송
→ 서버 탐지 결과 수신
→ Overlay 표시
```

전송 주기:
```text
0.5초 / 1초 기본값 / 2초
```

## 7. On-device Mode
Ultralytics YOLO Android 예제 구조를 기준으로 구현한다.

```text
model.tflite 로딩
labels.txt 로딩
metadata.json 로딩
CameraX 프레임 입력
TFLite 추론
YOLO 후처리
NMS
화면 좌표 변환
Overlay 표시
DetectionLog 서버 전송
```

## 8. 모델 업데이트
앱은 서버 최신 모델 정보를 조회하고, 로컬 모델보다 최신이면 다음 파일을 다운로드한다.

```text
model.tflite
labels.txt
metadata.json
```

다운로드 실패 시 기존 로컬 모델 또는 기본 내장 모델을 사용한다.

## 9. UI 스타일
- Material 3
- Light/Dark Theme 지원
- 카메라 화면은 다크 스타일 우선
- 상태 패널은 반투명 카드
- Bounding Box는 클래스별 색상
