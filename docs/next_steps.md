# MDetect Next Steps

## Priority 1
- Run the documented physical-phone Server Mode checklist against the active Step 10 YOLO model.
- Record one phone-originated `DetectionLog` with `model_version=step10_yolov8n_smoke_model`.
- Replace the Step 10 pretrained YOLOv8n smoke model with a project-trained `class_01/class_02/other` model when enough labeled data exists.
- Validate exported TFLite output shape and complete Android YOLO post-processing.
- Add inference timeout/rate limiting around `/api/detect/server/`.

## Priority 2
- Add robust DetectionLog sync from Android On-device Mode.
- Add detection history pagination and filters.
- Add training/export job cancellation and better progress reporting.

## Priority 3
- Move long-running training/export work to Celery or another durable worker.
- Add production deployment hardening for secrets, static/media, logs, and workers.
- Add CI checks for Django tests and Android debug build.

## Color/Product Class Training Next Steps
1. Confirm `soap_case_pink` / `soap_case_white` / `soap_case_mint` / `shampoo_case_white` / `other` exist in the Object Classes screen.
2. If a class is missing, an administrator creates it manually from the web screen.
3. Upload images by class.
4. Label class-specific Bounding Boxes.
5. Create a new DatasetVersion.
6. Run a new TrainingJob.
7. Validate in Server Mode.
8. After validation succeeds, run Android Model Export/Deployment.
9. Validate On-device Mode after YOLO TFLite decoding is implemented.
## Augmented Dataset Build Next Steps

1. Add more real source images before relying on 500-image augmented datasets.
2. Target at least 50 original images per class and use moderate augmentation.
3. Build an augmented DatasetVersion with color-safe augmentation enabled.
4. Train a YOLO model from the augmented DatasetVersion.
5. Review confusion matrix and class별 precision/recall.
6. Test the trained model with Server Mode first.
7. Review Detection Logs for white/mint and soap/shampoo confusion.
8. Add rotation/perspective augmentation only after robust box transformation tests are added.

## Step 17 Next Step

ObjectClass names now match the target class names. The next action is to run Dataset Build with:

```text
Name: soap_case_color_aug_500_v1
Use augmentation: checked
Target images per class: 500
Max augmentations per source image: 100
Color-safe augmentation: checked
```

Do not start TrainingJob until the augmented DatasetVersion is built successfully.

## Step 18 Next Step

Use the separated screen for augmentation:

```text
Augmented Dataset Build
/datasets/build/augmented/
```

Use regular Dataset Build only when you want a YOLO DatasetVersion from original labeled images without augmentation.

After building, open Dataset Versions and confirm:

```text
Type: augmented
Status: Built
Images: about 2500
```
