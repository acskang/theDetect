# MDetect Implementation Result

## Step 24 - Android Local Logout / Token Clear

Date: 2026-06-14

### Summary
- Added local Android logout through Home and Settings.
- Added a confirmation dialog before clearing session state.
- Clears access token, refresh token, device token, user id, username, phone number, approval status, connected state, and welcome message from DataStore. The last successful username/password remains saved for the next login form.
- Logout returns the app to the landing screen with disconnected/login-required state.
- Documented that server-side token blacklist and device-token revoke are not part of Step 24.

### Verification
- See the Step 24 completion report for command results.

### Step Boundary
Only Android local logout/token clear was implemented. Server logout API, refresh token blacklist, device-token revoke, Keystore storage, Dataset Build, TrainingJob, Server Mode inference, Model Update, and On-device decoder changes were not performed.

## Step 23 - Android Auth Real-device Test Preparation

Date: 2026-06-14

### Summary
- Performed server API smoke testing for signup, pending login rejection, shell approval, approved login, app session refresh, wrong device token rejection, default JWT refresh, protected-test, and health.
- Confirmed refresh token lifetime is 7 days.
- Confirmed Android debug APK builds at `mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk`.
- Added real-device auth test result and expanded Android auth manual test documentation.
- Fixed approval save handling so `approved_at` is persisted when approving by shell with `update_fields`.
- Improved Android auth failure text to include the server response body where available.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: passed.
- `python manage.py test accounts api`: passed.
- `python manage.py test`: passed.
- `cd mobile/MDetect && ./gradlew assembleDebug`: passed.
- `cd mobile/MDetect && ./gradlew testDebugUnitTest`: passed with `NO-SOURCE`.

### Step Boundary
Only auth test preparation, smoke validation, small auth-message/approval fixes, and documentation were changed. Dataset Build, TrainingJob, Server Mode inference, Model Update, and On-device decoder behavior were not changed.

## Step 22 - App Signup/Login/Session Auth

Date: 2026-06-14

### Summary
- Extended `AccountProfile` with approval status, admin approval metadata, device token, and last device login timestamp.
- Added API signup at `/api/auth/signup/` with duplicate username/phone checks, password confirmation, and Django password validation.
- Extended `/api/auth/login/` to require approved profiles and return user payload, welcome message, and server-generated `device_token`.
- Added `/api/auth/session/refresh/` for startup restore using `refresh_token + device_token`.
- Set SimpleJWT access token lifetime to 30 minutes and refresh token lifetime to 7 days with refresh rotation.
- Updated Android startup to begin disconnected, restore session with refresh/device token, show Login and Sign up screens, store tokens/user/device token, and display connected/welcome state.
- Preserved Server Mode, Model Update, Detection History, and On-device flows behind the refreshed access token.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations accounts`: created `accounts.0002_accountprofile_approval_status_and_more`.
- `python manage.py migrate`: passed.
- `python manage.py test accounts api`: 28 tests passed.
- `python manage.py test`: 103 tests passed.
- `cd mobile/MDetect && ./gradlew assembleDebug`: passed.
- `cd mobile/MDetect && ./gradlew testDebugUnitTest`: passed with `NO-SOURCE`.

### Step Boundary
Only signup/login/session restore authentication was implemented. Dataset Build, Training, Server Mode inference, Model Export, and On-device decoder logic were not changed.

## Step 21 - Project Settings Read-only Overview

Date: 2026-06-14

### Summary
- Replaced the Project Settings placeholder with a read-only system settings dashboard at `/project-settings/`.
- Added overview sections for service/runtime settings, upload policy, dataset defaults, augmentation defaults, training defaults, Android integration, active server model, deployed Android package, data summary, and system checks.
- Reads existing Django settings, DB rows, and file existence state without creating a ProjectSettings model or changing any schema.
- Added tests for login protection, empty active/deployed model states, data summary context, and system check rendering.

### Verification
- See the Step 21 completion report for the latest command results.

### Step Boundary
Only the Project Settings read-only overview was implemented. Editable settings, DB-backed configuration, migrations, Dataset Build changes, TrainingJob changes, and Android app changes were not performed.

## Step 01 - Project Setup

Date: 2026-06-11

### Summary
- Created the Django 5.2 project `theDetect` in the repository root.
- Created the required Django app shells: `accounts`, `core`, `datasets`, `labeling`, `training`, `models_registry`, `deployment`, `detection`, and `api`.
- Added the minimal settings needed for local sqlite3 development, template discovery, app registration, service metadata, and `project_data`.
- Added a Tailwind/HTMX/Alpine.js-ready base template and a basic Dashboard page.
- Created the `project_data/` storage directory structure required by the server design.

### Verification
- `python3 manage.py check`: passed.
- `python3 manage.py migrate`: passed.
- `python3 manage.py runserver 127.0.0.1:8011` plus `curl http://127.0.0.1:8011/`: Dashboard returned HTTP 200.

### Step Boundary
Only Step 01 project setup was implemented. Server core models, API behavior, labeling, training, model deployment, Android app work, and integration tests remain for later steps.

## Step 02 - Server Core

Date: 2026-06-11

### Summary
- Added core server models: `ObjectClass`, `UploadedImage`, `DatasetVersion`, and `DetectionLog`.
- Added an idempotent seed migration for `class_01`, `class_02`, and `other`.
- Added Tailwind-based console pages for Dashboard, Object Classes, Image Dataset, and API Test.
- Added Object Class create/edit/list views.
- Added multi-image upload and ZIP upload with extension checks, Pillow validation, upload size limit, and ZIP path traversal filtering.
- Added DRF/SimpleJWT endpoints for health, login, refresh, and protected API testing.
- Added an environment-driven MVP test user management command.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: passed with no changes detected after migrations were created.
- `python manage.py migrate`: passed.
- `python manage.py test datasets api`: 4 tests passed.
- `python manage.py runserver 127.0.0.1:8012` plus `curl`: Dashboard, Object Classes, Image Dataset, API Test, and `/api/health/` returned HTTP 200.
- JWT login, refresh, and protected-test were verified with `curl`.

### Step Boundary
Only Step 02 server core work was implemented. Bounding box labeling canvas, YOLO training, Android model conversion/deployment, Android app code, and integration testing remain for later steps.

## Step 03 - Labeling Workspace

Date: 2026-06-11

### Summary
- Added the `LabelBox` model in the `labeling` app and registered it in Django admin.
- Added authenticated Labeling Workspace pages at `/labeling/` and `/labeling/images/<image_id>/`.
- Added an Alpine.js-based image labeling editor for drawing, selecting, resizing, deleting, saving, and reloading bounding boxes.
- Added label save, complete, and next-image endpoints.
- Stores all LabelBox coordinates in original image pixel coordinates.
- Validates active object class, image existence, and coordinate bounds before saving.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations labeling`: created `labeling.0001_initial`.
- `python manage.py makemigrations`: passed with no changes detected after migration creation.
- `python manage.py migrate`: passed.
- `python manage.py test labeling`: 5 tests passed.
- Authenticated smoke check: Dashboard, Labeling Workspace list, Labeling editor, Object Classes, Image Dataset, and API Test returned HTTP 200.
- Authenticated label save API returned `{"saved": true, "count": 1}`.

### Step Boundary
Only Step 03 labeling workspace work was implemented. Dataset Build, YOLO training, Android model conversion/deployment, Android app code, and integration testing remain for later steps.

## Step 04 - Training Pipeline

Date: 2026-06-11

### Summary
- Added Dataset Build form and DatasetVersion list pages.
- Added LabelBox to YOLO label export with original-pixel to normalized-coordinate conversion.
- Added train/val/test split creation, image copy, label txt files, and `data.yaml` generation.
- Added class balance warning calculation and split-missing-class warnings stored on DatasetVersion.
- Added `TrainingJob` model, admin, form, list page, and detail page.
- Added background-thread YOLO runner using the `yolo detect train` command with `yolov8n.pt` fallback when `yolo11n.pt` fails.
- Added `TrainedModel` model, admin, Model Registry page, and active server model toggle.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations datasets training models_registry`: created DatasetVersion status, TrainingJob, and TrainedModel migrations.
- `python manage.py makemigrations`: passed with no changes detected after migration creation.
- `python manage.py migrate`: passed.
- `python manage.py test datasets training models_registry`: 9 tests passed.
- Authenticated smoke check: Dashboard, Dataset Build, DatasetVersion list, Training Jobs, Training Job Detail, Model Registry, Object Classes, Image Dataset, Labeling Workspace, and API Test returned HTTP 200.

### Step Boundary
Only Step 04 training pipeline work was implemented. Android model export, Android model deployment API, Android app code, and integration testing remain for later steps.

## Step 05 - Android Model Export / Model Deployment

Date: 2026-06-11

### Summary
- Added `AndroidModelPackage` in the `deployment` app.
- Added Android model export UI, package list, package detail, and deploy action.
- Added a TFLite export runner that creates `labels.txt`, `metadata.json`, and runs `yolo export ... format=tflite`.
- Added safe failure handling for export errors with status and error message persistence.
- Added single deployed Android package handling.
- Added JWT-protected latest Android model info API and file download APIs.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations deployment`: created `deployment.0001_initial`.
- `python manage.py makemigrations`: passed with no changes detected after migration creation.
- `python manage.py migrate`: passed.
- `python manage.py test deployment api`: 14 tests passed.
- Authenticated smoke check: Dashboard, Android Model Export, Android Package list/detail, Object Classes, Image Dataset, Labeling Workspace, Dataset Build, Training Jobs, and Model Registry returned HTTP 200.
- JWT-protected API smoke check: latest model info, `model.tflite`, `labels.txt`, and `metadata.json` downloads returned HTTP 200.

### Step Boundary
Only Step 05 Android model export/deployment server work was implemented. Android app implementation and full integration tests remain for later steps.

## Step 06 - Android App

Date: 2026-06-11

### Summary
- Created the Android project at `mobile/MDetect`.
- Implemented Kotlin + Jetpack Compose app structure with package `com.thesysm.mdetect`.
- Added Splash, Home, Camera Detection, Detection History, Model Update, and Settings screens.
- Added CameraX Preview with runtime camera permission handling.
- Added JWT auto-login client using the MVP test account defaults.
- Added DataStore-backed server URL, mode, interval, threshold, and credential settings.
- Added Retrofit/OkHttp API client for health, login, refresh, server detection, detection history, latest model, and model file downloads.
- Added Android model package download flow that saves to `filesDir/models/current/` after successful temporary downloads.
- Added Server Mode frame upload structure with CameraX YUV frame conversion, rotation, long-side resize, and JPEG quality 80.
- Added On-device Mode TFLite Interpreter load/NMS/fallback structure.

### Verification
- `./gradlew assembleDebug`: passed.
- Debug APK created at `mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk`.

### Step Boundary
Only Step 06 Android app MVP work was implemented. Full device/server integration testing remains for Step 07.

## Step 07 - Integration Test / Stabilization

Date: 2026-06-11

### Summary
- Verified server-wide checks, migrations, full Django test suite, and Android debug build.
- Added minimum JWT-protected Server Detection API at `/api/detect/server/` that returns stable JSON without requiring active YOLO inference.
- Added minimum JWT-protected Detection History API at `/api/detection-logs/`.
- Updated Android Detection History client to match the server `{ "results": [...] }` response shape.
- Confirmed Android API client endpoint paths match Django endpoints for auth, health, model update/download, server detection, and detection history.
- Created a smoke test account and fake deployed Android model package for integration checks without hardcoding server credentials.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: passed.
- `python manage.py migrate`: passed.
- `python manage.py test`: 30 tests passed.
- Authenticated page smoke: Dashboard, Object Classes, Image Dataset, Labeling, Dataset Build, Dataset Versions, Training Jobs, Model Registry, Android Model Export, Android Packages, API Test, and package detail returned HTTP 200.
- JWT/API smoke: health, login, refresh, protected-test, latest Android model, model file downloads, server detection, and detection logs returned HTTP 200.
- `cd mobile/MDetect && ./gradlew assembleDebug`: passed.

### Step Boundary
Only Step 07 integration stabilization was performed. Full YOLO server inference, full Android TFLite output decoding, and production deployment hardening remain future work.

## Step 08 - Server-side YOLO Inference

Date: 2026-06-11

### Summary
- Replaced the MVP-only `/api/detect/server/` response with real active-server-model inference when `TrainedModel.is_active_server_model=True`.
- Added a YOLO inference service with Pillow image validation, allowed extension checks, Ultralytics model loading, and in-memory model caching.
- Converts Ultralytics detection boxes into Android-compatible JSON using original request-image pixel coordinates.
- Uses `TrainedModel.class_names_json` first for class names, then YOLO model names, then `class_<id>` fallback.
- Saves server inference results to `DetectionLog` with top class, confidence, app version, device info, user, and uploaded image when possible.
- Keeps stable non-500 JSON responses for no active model, missing model files, YOLO import/load/inference failures, and DetectionLog save failures.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: passed with no changes detected.
- `python manage.py test api detection models_registry`: 15 tests passed.

### Step Boundary
Only Step 08 server-side YOLO inference work was implemented. Android app changes, Android on-device decoding, Celery/Redis, training pipeline rewrites, and Android model export rewrites were not performed.

## Step 09 - Android Server Mode Real-device Test Preparation

Date: 2026-06-12

### Summary
- Confirmed `/api/detect/server/` active model behavior and Model Registry active-model UI flow.
- Added real-image curl test documentation for JWT login and Server Mode inference.
- Expanded the Android real-device guide with LAN server setup, phone server URL rules, firewall checks, active model checks, and APK location.
- Added a dedicated Server Mode test guide for active model setup, no-active-model handling, curl testing, Android Settings, and Camera Detection testing.
- Updated Android Server Mode client parsing so `model_available=false` and server `message` are surfaced in the Camera status panel instead of being silently treated as empty detections.
- Added `device_info` and `app_version` multipart fields from Android Server Mode requests.
- Updated Settings connection test status so the result is visible in the shared status text.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: passed with no changes detected.
- `python manage.py test api detection models_registry`: passed.
- `cd mobile/MDetect && ./gradlew assembleDebug`: passed.
- Authenticated smoke check confirmed `/api/detect/server/` returns clear `model_available=false` JSON when no active server model exists.

### Step Boundary
Only Step 09 real-device Server Mode test preparation and minimal UX/message handling were performed. Android UI redesign, On-device YOLO decoding, Celery/Redis, training/export rewrites, and production deployment automation were not performed.

## Step 10 - Active YOLO Server Mode Verification

Date: 2026-06-12

### Summary
- Added management commands for active model inspection, active model selection, and server detection smoke testing.
- Registered a smoke `TrainedModel` using Ultralytics `yolov8n.pt` and set it as the active server model.
- Verified the active model points to an existing `.pt` file.
- Ran real YOLO inference with the Ultralytics `bus.jpg` test image through both the management smoke command and the HTTP `/api/detect/server/` API.
- Confirmed `model_available=true`, `message=ok`, non-empty `detections`, and DetectionLog persistence.
- Confirmed DetectionLog saved `mode=server`, `model_version`, `detections_json`, `top_class`, `top_confidence`, `device_info`, `app_version`, and image.
- Confirmed no-active-model response still returns clear non-500 JSON.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: passed with no changes detected.
- `python manage.py test api detection models_registry`: 18 tests passed.
- `python manage.py smoke_server_detect --image <bus.jpg> --username mdetect_smoke --device-info step10-command --app-version step10-smoke`: returned `model_available=true`, `detections_count=6`, and `log_id=2`.
- HTTP curl against `POST /api/detect/server/`: returned `model_available=true`, `model_version=step10_yolov8n_smoke_model`, `detections` count 6, `message=ok`, and `log_id=3`.

### Step Boundary
Only Step 10 active YOLO Server Mode verification and small command/test/documentation support were implemented. Android On-device decoding, Celery/Redis, training/export rewrites, Android UI redesign, and model export rewrites were not performed.

## Step 11 - Android Real-device Server Mode Test Preparation

Date: 2026-06-12

### Summary
- Confirmed the active smoke model is `step10_yolov8n_smoke_model` and its `model_path` points to a usable `.pt` file.
- Rebuilt the Android debug APK for real-device Server Mode testing.
- Added a minimal Android status-panel improvement so successful Server Mode responses show `message`, `model_available`, and `log_id`.
- Expanded real-device documentation for server startup, LAN IP discovery, firewall checks, APK install, Settings server URL setup, Camera Detection, and DetectionLog verification.
- Clarified that the active smoke model is pretrained YOLOv8n COCO, so detections such as `person`, `bus`, `bottle`, and `cup` are expected.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: passed with no changes detected.
- `python manage.py test api detection models_registry`: passed.
- `cd mobile/MDetect && ./gradlew assembleDebug`: passed.
- `python manage.py list_trained_models`: confirmed active `step10_yolov8n_smoke_model` with `usable_pt=True`.

### Step Boundary
Only Step 11 Android real-device Server Mode test preparation, documentation, APK build, and minimal status message handling were performed. Android On-device decoding, Celery/Redis, training/export rewrites, Android UI redesign, and model export rewrites were not performed.

## Step 12 - Color/Product Class Training Design

Date: 2026-06-13

### Summary
- Confirmed the target color/product class policy for `soap_case_pink`, `soap_case_white`, `soap_case_mint`, `shampoo_case_white`, and `other`.
- Added a color/product class separation training design document.
- Added a Codex execution prompt for color/product class training preparation and validation.
- Documented that Step 12 is documentation-only and does not affect existing server, Android, or DB functionality.
- No ObjectClass records were automatically created or modified.
- No migrations were created.
- No code was modified.
- Documented color augmentation cautions.
- Documented the confusion risk between `soap_case_white` and `shampoo_case_white`.
- Documented a Server Mode first validation policy and noted that On-device validation should follow after YOLO TFLite decoding is completed.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: passed with no changes detected.

### Step Boundary
Only Step 12 documentation was performed. Django server code, Android code, DB schema, migrations, APIs, training pipeline, Dataset Build, YOLO Training, settings, dependencies, and production data were not changed.

## Step 13 - Color/Product ObjectClass Status Check

Date: 2026-06-13

### Summary
- Checked the current ObjectClass list for the target color/product classes.
- Confirmed exact `name` match exists for `other`.
- Confirmed `soap_case_pink`, `soap_case_white`, `soap_case_mint`, and `shampoo_case_white` currently exist only as `display_name` values on `class_01`, `class_02`, `class_03`, and `class_04`.
- Documented that exact `name` matches are missing for `soap_case_pink`, `soap_case_white`, `soap_case_mint`, and `shampoo_case_white`.
- Added manual web-screen creation guidance with recommended values for name, display name, description, color, active flag, and sort order.
- Did not auto-create, modify, or delete ObjectClass records.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: passed with no changes detected.

### Step Boundary
Only Step 13 ObjectClass state inspection and documentation were performed. No DB data was changed, no code was modified, no migration was created, and no training or Dataset Build action was run.
## Step 15 - Augmented Dataset Build

- Added optional Augmented Dataset Build support without changing the default Dataset Build path.
- Added Dataset Build options: Use augmentation, Target images per class, Max augmentations per source image, and Color-safe augmentation.
- Added color-safe augmentation service for brightness, contrast, blur, noise, horizontal shift, vertical shift, and scale.
- Bounding boxes are transformed with scale/shift, clipped to image boundaries, and skipped when invalid or too small.
- Original UploadedImage and LabelBox records are not modified.
- Augmented samples stay in the same train/val/test split as their source image to reduce leakage.
- Augmentation settings are stored in DatasetVersion.build_config_json without DB schema changes.
- Added warnings for low source image counts, 50x target expansion, and color/product confusion risks.
- Added tests for augmentation-off compatibility, augmented target generation, YOLO label range, source split leakage prevention, and color-safe policy.
- Added docs/augmented_dataset_build_design.md and docs/augmented_dataset_build_manual.md.
## Step 16 - Augmented Dataset Prebuild Check

- Checked ObjectClass `name` and `display_name` state before creating an augmented DatasetVersion.
- Checked class별 LabelBox count and distinct labeled UploadedImage count.
- Checked invalid LabelBox conditions.
- Result: Dataset Build must not be run yet because four ObjectClass `name` values are still `class_01` through `class_04`, even though display names match target class names.
- Dataset Build was not executed.
- TrainingJob was not executed.
- No DB data was changed.
- No code was changed.
- No migration was created.
## Step 17 - ObjectClass Rename For Color/Product Training

- Safely renamed ObjectClass `name` values from temporary names to final color/product target class names.
- Renamed `class_01` to `soap_case_pink`.
- Renamed `class_02` to `soap_case_white`.
- Renamed `class_03` to `soap_case_mint`.
- Renamed `class_04` to `shampoo_case_white`.
- Kept `other` unchanged.
- Confirmed target name collisions did not exist before rename.
- Confirmed class_01 through class_04 each existed exactly once and display names matched target names.
- Confirmed invalid LabelBox count was 0 before and after rename.
- Confirmed LabelBox and labeled image counts remained 5 per target class after rename.
- Confirmed Augmented Dataset Build readiness after rename.
- Dataset Build was not executed.
- TrainingJob was not executed.
- No migration was created.
- No code was changed.
## Step 18 - Dataset Build Screen Separation

- Separated original Dataset Build and Augmented Dataset Build at the screen and menu level.
- Kept `/datasets/build/` for original labeled-image DatasetVersion builds only.
- Added `/datasets/build/augmented/` for augmentation-based DatasetVersion builds.
- Removed augmentation options from the original Dataset Build screen.
- Removed the `Use augmentation` checkbox from the augmented screen because the screen itself always runs augmentation.
- Added Augmented Dataset Build menu item.
- Added Dataset Versions menu item.
- Added Dataset Versions Type and Images columns.
- Stored `build_config_json.build_type = "original"` for original builds.
- Stored `build_config_json.build_type = "augmented"` for augmented builds.
- Preserved existing DatasetVersion, LabelBox, UploadedImage, TrainingJob, Android, and Server Mode API behavior.
- No DB schema change or migration was created.

## Step 19 - Android On-device YOLO TFLite 1차 구현

Date: 2026-06-14

### Summary
- Implemented first-pass Android On-device YOLO TFLite inference in `OnDeviceDetector`.
- Added loading for downloaded `model.tflite`, `labels.txt`, and `metadata.json` from `filesDir/models/current/`.
- Added TFLite input/output tensor shape and dtype inspection for status/logging.
- Added Camera JPEG to Bitmap decode in the On-device ViewModel path.
- Added letterbox resize preprocessing and RGB input buffer creation.
- Added FLOAT32 input support and basic UINT8 input support.
- Added raw YOLO output decoding for `[1, channels, boxes]` and `[1, boxes, channels]`.
- Added support for both `4 + num_classes` and `5 + num_classes` output channel layouts.
- Added confidence threshold filtering, class-wise NMS, max detection limiting, and bbox restore to original bitmap coordinates.
- Connected On-device results to the existing `DetectionBox` state and overlay.
- Added fallback status messages for missing models, metadata/labels issues, unsupported tensor shapes, bitmap decode failure, and inference failure.
- Documented the On-device preprocessing/decoding design, result, real-device checklist, limitations, and next steps.

### Verification
- `cd mobile/MDetect && ./gradlew assembleDebug`: passed.

### Step Boundary
Only Android On-device TFLite preprocessing, decoding, ViewModel connection, and documentation were changed. Django server code, migrations, Dataset Build, TrainingJob, Model Export server logic, Server Mode API, Model Update download flow, and Android UI layout were not changed.

## Step 20 - Android On-device Model Validation Preparation

Date: 2026-06-14

### Summary
- Added local model file state reporting for Android Model Update.
- Model Update now shows local model version, latest server model version, downloaded file presence, labels count, and local model size.
- Added On-device debug state for model version, input tensor shape/dtype, output tensor count/shape/dtype, decoder layout, labels count, metadata input size, detections count, and last error.
- Camera Detection status panel now shows On-device input shape, output shape, decoder layout, downloaded file state, and last error.
- Standardized Logcat tags for validation: `MDetectOnDevice`, `MDetectModelUpdate`, and `MDetectCamera`.
- On-device logs now include model path, metadata path, labels path, tensor info, decoder layout, inference time, detections count, and error summary.
- Confirmed the local DB has one deployed Android package: `id=2`, `model_version=mdetect_integration_001`, `status=completed`.
- Added On-device model validation guide with deployed package check, Model Update download check, real-device test steps, Logcat command, and shape mismatch data collection list.

### Verification
- `cd mobile/MDetect && ./gradlew assembleDebug`: passed.
- `cd mobile/MDetect && ./gradlew testDebugUnitTest`: passed with `NO-SOURCE`.
- `python3 manage.py check`: passed.
- `python3 manage.py makemigrations --check`: passed with no changes detected.
- Deployed package shell check returned `mdetect_integration_001`.

### Step Boundary
Only Android validation visibility, Logcat diagnostics, Model Update status display, and documentation were changed. Django server code, DB schema, migrations, Dataset Build, TrainingJob, Model Export server logic, Server Mode API, On-device decoder logic, GPU/NNAPI, and Android UI structure were not changed.

## Step 25 - Server Logout / Refresh Revoke / Device Token Revoke

Date: 2026-06-14

### Summary
- Added `POST /api/auth/logout/`.
- Enabled SimpleJWT token blacklist support.
- Logout blacklists the submitted refresh token and clears the matching `AccountProfile.device_token`.
- Session restore now rejects empty or revoked device tokens.
- Android logout now calls the server logout API before local DataStore clear.
- Android still completes local logout when the server logout call fails.
- Added server tests for logout success, wrong device token rejection, pending profile rejection, and refresh reuse failure.
- Added logout/revoke documentation and manual Android test steps.

### Verification
- `python manage.py check`: passed.
- `python manage.py makemigrations accounts`: no changes detected.
- `python manage.py migrate`: applied SimpleJWT `token_blacklist` migrations.
- `python manage.py test accounts api`: passed.
- `python manage.py test`: passed.
- `cd mobile/MDetect && ./gradlew assembleDebug`: passed.
- `cd mobile/MDetect && ./gradlew testDebugUnitTest`: passed with `NO-SOURCE`.
- Logout smoke confirmed login 200, logout 200, server device token cleared, session refresh after logout 401, and JWT refresh reuse 401.

### Step Boundary
Only auth logout/revoke behavior, Android logout API integration, tests, and documentation were changed. Dataset Build, TrainingJob, Server Mode inference, On-device decoder, and Android UI structure were not changed.

## Step 26 - Homepage Copy Update

Date: 2026-06-14

### Summary
- 홈페이지 메인 제목을 "실시간 스마트폰 객체탐지 시스템"으로 변경.
- 설명 문구를 MDetect의 범용 모바일 객체탐지 플랫폼 목적에 맞게 수정.
- 코드 로직, DB, API, Android 앱 변경 없음.

### Step Boundary
Only homepage copy and implementation documentation were changed.

## Step 27 - Homepage Process Cards with Icons Update

Date: 2026-06-14

### Summary
- 기존 Mode/Model/Console 상태 카드 3개를 제거하고 6단계 작업 절차 카드로 교체.
- 각 카드에 의미를 전달하는 심플한 inline SVG 심볼 아이콘 추가.
- 작업 절차: 이미지 준비 -> B-Box 라벨링 -> 데이터셋 제작 -> 학습 모델 생성 -> 스마트폰용 모델 생성 -> 스마트폰 적용.
- 외부 이미지/패키지 추가 없음.
- 코드 로직, DB, API, Android 앱 변경 없음.

### Step Boundary
Only homepage process-card content, inline SVG icons, and documentation were changed.
