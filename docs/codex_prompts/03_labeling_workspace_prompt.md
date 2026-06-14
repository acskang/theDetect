# Codex Prompt 03 - Labeling Workspace

## 목표
서버 웹에서 직접 Bounding Box 라벨링 기능을 구현한다.

## 기술
Django Template + HTMX + Alpine.js + Tailwind CSS

## 구현
- LabelBox 모델
- 이미지 목록/상태 필터
- Canvas 기반 박스 생성/수정/삭제
- class_01/class_02/other 선택
- 원본 이미지 기준 픽셀 좌표 저장
- 저장된 라벨 재로딩

## 검증
- x_min < x_max
- y_min < y_max
- 좌표가 이미지 범위를 벗어나지 않음

## 완료 조건
- 라벨 저장/수정/삭제 가능
- 다음 이미지 이동 가능
- DB 좌표 확인 가능
