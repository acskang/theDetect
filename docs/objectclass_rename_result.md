# ObjectClass Rename Result

## Check Time

2026-06-13 23:26:44 KST

## Reason

Step 16 found that `display_name` matched the target classes, but `ObjectClass.name` still used temporary names:

```text
class_01
class_02
class_03
class_04
```

YOLO `data.yaml` and model class names use `ObjectClass.name`, so the names were changed to the final target class names before Augmented Dataset Build.

## Before State

| id | before name | display_name | description | color | active | sort_order | LabelBox count | labeled image count |
|---:|---|---|---|---|---|---:|---:|---:|
| 1 | class_01 | soap_case_pink | 1. soap case pink | #ed333b | true | 10 | 5 | 5 |
| 2 | class_02 | soap_case_white | 2. soap case white | #ffffff | true | 20 | 5 | 5 |
| 4 | class_03 | soap_case_mint | 3. soap case mint | #8ff0a4 | true | 30 | 5 | 5 |
| 5 | class_04 | shampoo_case_white | 4. shampoo case round | #f6f5f4 | true | 40 | 5 | 5 |
| 3 | other | other | Negative or non-target object class for reducing false positives. | #f97316 | true | 50 | 5 | 5 |

## Safety Check Result

| condition | result |
|---|---|
| target names did not already exist | pass |
| class_01 through class_04 each existed exactly once | pass |
| class_01 through class_04 display_name matched target names | pass |
| invalid LabelBox count was 0 | pass |
| class_01 through class_04 LabelBox connections existed | pass |
| existing class_01/class_02 artifacts were smoke/integration test artifacts | pass |
| active server model was unrelated COCO smoke model | pass |
| DetectionLog did not contain class_01 through class_04 results | pass |

Existing artifacts containing `class_01` or `class_02`:

- `step04_smoke_dataset`
- `step05_smoke_dataset`
- `integration_dataset`
- `step04_smoke_job`
- `step05_smoke_job`
- `integration_job`
- `step04_smoke_model`
- `step05_smoke_model`
- `integration_model`
- `mdetect_step05_smoke_001`
- `mdetect_integration_001`

These were treated as smoke/test/integration artifacts, not current production color/product class models.

## Actual Changes

```text
class_01 -> soap_case_pink
class_02 -> soap_case_white
class_03 -> soap_case_mint
class_04 -> shampoo_case_white
other    -> other 유지
```

No ObjectClass was created or deleted.

## After State

| id | name | display_name | description | color | active | sort_order | LabelBox count | labeled image count |
|---:|---|---|---|---|---|---:|---:|---:|
| 1 | soap_case_pink | soap_case_pink | 1. soap case pink | #ed333b | true | 10 | 5 | 5 |
| 2 | soap_case_white | soap_case_white | 2. soap case white | #ffffff | true | 20 | 5 | 5 |
| 4 | soap_case_mint | soap_case_mint | 3. soap case mint | #8ff0a4 | true | 30 | 5 | 5 |
| 5 | shampoo_case_white | shampoo_case_white | 4. shampoo case round | #f6f5f4 | true | 40 | 5 | 5 |
| 3 | other | other | Negative or non-target object class for reducing false positives. | #f97316 | true | 50 | 5 | 5 |

## LabelBox Connection Result

LabelBox connections were preserved because only `ObjectClass.name` and `display_name` were updated. ObjectClass primary keys did not change.

| class | LabelBox count | labeled image count |
|---|---:|---:|
| soap_case_pink | 5 | 5 |
| soap_case_white | 5 | 5 |
| soap_case_mint | 5 | 5 |
| shampoo_case_white | 5 | 5 |
| other | 5 | 5 |

Invalid LabelBox count after rename:

```text
0
```

## Augmented Dataset Build Readiness

Status:

```text
가능
```

Reason:

- all five target ObjectClass names exist exactly once
- each class has at least 5 LabelBox records
- each class has at least 5 distinct labeled images
- invalid LabelBox count is 0

## Dataset Build Inputs

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

Run Augmented Dataset Build with the inputs above, then create a YOLO TrainingJob from the built DatasetVersion.
