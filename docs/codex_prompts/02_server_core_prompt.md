# Codex Prompt 02 - Server Core

## 목표
MDetect 서버의 핵심 모델, JWT 인증, 관리자 콘솔, 이미지 업로드를 구현한다.

## 구현
- ObjectClass, UploadedImage, DatasetVersion, DetectionLog 기본 모델
- 초기 클래스 seed: class_01, class_02, other
- JWT login/refresh API
- Dashboard, Object Classes, Image Dataset 화면
- 다중 이미지 업로드
- ZIP 업로드

## 주의
- ZIP path traversal 방어
- jpg/jpeg/png/webp만 허용
- 업로드 파일 크기 제한
- 기존 기능 삭제 금지

## 완료 조건
- ObjectClass CRUD
- 이미지 다중 업로드
- ZIP 업로드
- JWT 동작
- Dashboard 통계 표시
