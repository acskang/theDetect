# Augmented Dataset Build Screen Manual

## Open The Screen

Use the left menu:

```text
Augmented Dataset Build
```

URL:

```text
/datasets/build/augmented/
```

## What This Screen Does

This screen creates a YOLO DatasetVersion by augmenting labeled source images and transforming Bounding Boxes together.

It does not modify:

- UploadedImage
- LabelBox
- existing DatasetVersion
- TrainingJob

Generated images and labels are written only under the new DatasetVersion output folder.

## Inputs

Recommended first trial:

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

Target images per class:
500

Max augmentations per source image:
100

Color-safe augmentation:
checked

Build memo:
원본 class별 5장, 총 25장 기준. class별 500장 목표 증강. hue/saturation 증강 제외. Server Mode 1차 검증용.
```

## Preview

The screen shows current source image counts per class and expected target counts.

Example:

```text
soap_case_pink      original 5 -> target 500
soap_case_white     original 5 -> target 500
soap_case_mint      original 5 -> target 500
shampoo_case_white  original 5 -> target 500
other               original 5 -> target 500
```

## Important Warning

Class별 5장을 500장으로 증강하는 것은 기술적으로 가능하지만 overfitting 위험이 높다.

This build should be treated as a smoke/trial dataset. For better accuracy, collect at least 50 original images per class and use about 10x augmentation.

## After Build

1. Open Dataset Versions.
2. Confirm Type is `augmented`.
3. Confirm status is Built.
4. Start Training Jobs only after the DatasetVersion is built successfully.
5. Validate the trained model in Server Mode before Android deployment.
