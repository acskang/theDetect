# MDetect 색상별/제품별 객체 class 분리 학습 실행 프롬프트

## 프롬프트 본문

```text
너는 MDetect 프로젝트에서 색상 또는 제품 유형만 다른 유사 객체를 서로 다른 class로 학습시키는 작업을 보조한다.

대상 class는 다음이다.

- soap_case_pink
- soap_case_white
- soap_case_mint
- shampoo_case_white
- other

중요:
기존 기능을 절대 깨뜨리지 마라.
기존 DB schema, migration, 서버 API, Android 앱 코드를 수정하지 마라.
기존 ObjectClass, UploadedImage, LabelBox, DatasetVersion, TrainingJob, TrainedModel을 자동 변경하지 마라.
모든 class 생성/수정은 관리자가 웹 화면에서 명시적으로 수행한다.
Codex는 우선 상태 점검, 안내, 문서화, 필요한 최소 검증만 수행한다.
```

## 작업 항목

```text
1. Object Classes에 5개 class 존재 여부 확인
2. 없는 class는 자동 생성하지 말고, 생성 방법을 안내한다.
3. Image Dataset 업로드 상태 확인
4. Labeling Workspace 라벨 수 확인
5. class별 라벨 수 통계 확인
6. soap_case_white와 shampoo_case_white 혼동 가능성 점검
7. Dataset Build 전 class balance warning 확인
8. train/val/test split별 class 포함 여부 확인
9. YOLO TrainingJob 실행 전 설정 추천
10. 학습 완료 후 confusion matrix와 class별 성능 확인
11. Model Registry에서 active model 지정은 사용자 확인 후 수행
12. /api/detect/server/ curl 테스트
13. Android Server Mode 실기기 테스트
14. Android Model Export/Deployment는 Server Mode 검증 후 진행
```

## 추천 학습 설정

```text
base model: yolov8n.pt 또는 yolo11n.pt
imgsz: 640
epochs: MVP 50, 실제 100 이상 검토
batch: 16 또는 GPU 메모리에 맞게 조정
device: cuda 가능 시 cuda, 아니면 auto
patience: 20
workers: auto
```

## 색상/제품 class 학습 시 주의사항

```text
- 색상 augmentation 과다 금지
- white/mint 혼동 주의
- soap_case_white와 shampoo_case_white 혼동 주의
- 각 class별 데이터 수 균형 유지
- other class 과다 편향 주의
- 조명 조건 다양화
- 흰색 제품은 형태 차이가 잘 드러나는 각도를 충분히 확보
- 기존 active model은 사용자 확인 없이 변경하지 않는다.
- 기존 deployed Android model은 사용자 확인 없이 변경하지 않는다.
```

## 완료 보고 형식

```text
[색상별/제품별 class 학습 준비/검증 완료 보고]

1. ObjectClass 상태
2. 이미지 업로드 상태
3. 라벨링 상태
4. class별 라벨 수
5. soap_case_white vs shampoo_case_white 구분 데이터 상태
6. Dataset Build 결과
7. TrainingJob 결과
8. Model Registry active model
9. Server Mode API 테스트 결과
10. Android Server Mode 테스트 결과
11. 기존 기능 영향 여부
12. 남은 이슈
13. 다음 개선 작업
```
