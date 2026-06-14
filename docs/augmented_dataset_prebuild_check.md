# Augmented Dataset Prebuild Check

## Check Time

2026-06-13 23:23:25 KST

## Scope

This Step 16 check only inspected current ObjectClass, LabelBox, and UploadedImage-related labeling state before creating an augmented DatasetVersion.

No Dataset Build was executed. No TrainingJob was executed. No DB data was changed.

## Target Classes

The target model class names are:

```text
soap_case_pink
soap_case_white
soap_case_mint
shampoo_case_white
other
```

## Current ObjectClass State

| id | name | display_name | active | sort_order |
|---:|---|---|---|---:|
| 1 | class_01 | soap_case_pink | true | 10 |
| 2 | class_02 | soap_case_white | true | 20 |
| 4 | class_03 | soap_case_mint | true | 30 |
| 5 | class_04 | shampoo_case_white | true | 40 |
| 3 | other | other | true | 50 |

## Target Class Match Result

Current state is **not ready** for Augmented Dataset Build.

The display names match the target labels, but the actual `ObjectClass.name` values do not match for four classes.

| target class | exact `name` exists | current matching display_name |
|---|---:|---|
| soap_case_pink | no | class_01 / soap_case_pink |
| soap_case_white | no | class_02 / soap_case_white |
| soap_case_mint | no | class_03 / soap_case_mint |
| shampoo_case_white | no | class_04 / shampoo_case_white |
| other | yes | other / other |

Important:

```text
현재 display_name은 맞지만 name이 목표 class와 다르다.
YOLO class name 기준을 정확히 하려면 Object Classes 화면에서 name을 수동 수정한 뒤 다시 Step 16을 실행해야 한다.
```

## LabelBox Count By Current ObjectClass.name

| current name | LabelBox count |
|---|---:|
| class_01 | 5 |
| class_02 | 5 |
| class_03 | 5 |
| class_04 | 5 |
| other | 5 |

## Labeled Image Count By Current ObjectClass.name

This counts distinct UploadedImage records connected through LabelBox.

| current name | labeled image count |
|---|---:|
| class_01 | 5 |
| class_02 | 5 |
| class_03 | 5 |
| class_04 | 5 |
| other | 5 |

## Invalid Box Check

Checked invalid conditions:

```text
x_min >= x_max
y_min >= y_max
x_min < 0
y_min < 0
x_max > image_width
y_max > image_height
object_class 없음
image 없음
```

Result:

```text
invalid LabelBox count: 0
```

## Augmentation Risk

The current dataset has 5 labeled source images per current class.

```text
class별 5장을 500장으로 증강하는 것은 기술적으로 가능하지만 overfitting 위험이 높다.
이번 학습은 1차 smoke/trial 목적이다.
실서비스 정확도를 위해서는 class별 원본 50장 이상을 확보하고 10배 증강하는 것이 더 좋다.
```

## Augmented Dataset Build Readiness

Status:

```text
Build 불가능
```

Reason:

```text
ObjectClass.name values do not exactly match the target class names.
```

Do not run Dataset Build yet.

## Required Manual Fix

Use the web UI. Do not change DB rows directly.

```text
Object Classes 화면
→ class_01 Edit
→ Name을 soap_case_pink로 변경
→ Display name도 soap_case_pink 유지
→ Save

class_02 → soap_case_white
class_03 → soap_case_mint
class_04 → shampoo_case_white
other → 그대로 유지
```

After this manual fix, run Step 16 again before Dataset Build.

## Dataset Build Inputs After Readiness Is Fixed

Use these values only after ObjectClass names match exactly and Step 16 is rerun successfully.

```text
Name:
soap_case_color_aug_500_v1

Description:
soap_case_pink, soap_case_white, soap_case_mint, shampoo_case_white, other 5개 class를 class별 500장 목표로 color-safe augmentation build한 1차 학습용 dataset

Train ratio:
80

Val ratio:
10

Test ratio:
10

Random seed:
42

Include only labeled images:
checked

Exclude invalid boxes:
checked

Use augmentation:
checked

Target images per class:
500

Max augmentations per source image:
100

Color-safe augmentation:
checked

Build memo:
원본 class별 5장, 총 25장 기준. class별 500장 목표 증강. hue/saturation 증강 제외. Server Mode 1차 검증용.
```

## Next Step

1. Manually fix ObjectClass.name values in Object Classes.
2. Rerun Step 16.
3. If all class names match and invalid box count remains 0, run Augmented Dataset Build.
4. Use the created DatasetVersion for YOLO Training Jobs.
5. Validate the trained model in Server Mode before Android deployment.

## Step 17 Update

2026-06-13 23:26:44 KST

ObjectClass names were safely renamed:

```text
class_01 -> soap_case_pink
class_02 -> soap_case_white
class_03 -> soap_case_mint
class_04 -> shampoo_case_white
other    -> other 유지
```

Post-rename prebuild status:

```text
Augmented Dataset Build 가능
```

Post-rename counts:

| class | LabelBox count | labeled image count |
|---|---:|---:|
| soap_case_pink | 5 | 5 |
| soap_case_white | 5 | 5 |
| soap_case_mint | 5 | 5 |
| shampoo_case_white | 5 | 5 |
| other | 5 | 5 |

Invalid LabelBox count remains 0.
