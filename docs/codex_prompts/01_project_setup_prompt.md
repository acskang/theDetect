# Codex Prompt 01 - Project Setup

## 목표
Django 5.2 기반 서버 프로젝트 `theDetect`의 기본 구조를 준비한다.

## 환경
```text
Root: /home/cskang/ganzskang/theDetect
venv: dj5
DB: sqlite3
Docs: ./docs
URL: https://detect.thesysm.com
```

## 작업
1. 현재 디렉토리와 기존 파일을 먼저 확인한다.
2. 기존 파일을 절대 삭제하지 않는다.
3. Django 앱을 생성한다: accounts, core, datasets, labeling, training, models_registry, deployment, detection, api.
4. Tailwind/HTMX/Alpine.js 기반 base template을 만든다.
5. project_data 디렉토리 구조를 만든다.
6. Dashboard 기본 화면을 만든다.
7. `python manage.py check`, `migrate`를 통과시킨다.

## 완료 조건
- Dashboard 200 응답
- migrate 성공
- check 통과
- docs에 setup 결과 기록
