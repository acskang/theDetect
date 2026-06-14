# Codex Prompt 05 - Android App

## 목표
Kotlin + Jetpack Compose 기반 theDetect Android 앱을 구현한다.

## 화면
Splash, Home, Camera Detection, Detection History, Model Update, Settings

## 구현
- CameraX Preview
- Server Mode
- On-device Mode 기본 구조
- JWT 자동 로그인
- 서버 URL 설정
- Debug/Release 서버 주소 분리
- Retrofit/OkHttp Interceptor
- Detection Overlay

## Server Mode
프레임을 긴 변 1280px 이하로 리사이즈하고 JPEG quality 80으로 압축해 서버로 전송한다.
전송 주기는 0.5초/1초/2초 설정 가능, 기본 1초.

## On-device Mode
Ultralytics YOLO Android 예제 구조 기반으로 TFLite 로딩, YOLO 후처리, NMS, Overlay 표시를 구현한다.

## 완료 조건
- 앱 빌드 성공
- 자동 로그인 성공
- CameraX Preview 표시
- Server Mode API 호출 가능
- Overlay 표시 가능
