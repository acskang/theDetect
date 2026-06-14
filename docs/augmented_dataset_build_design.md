# Augmented Dataset Build Design

## Purpose

Augmented Dataset Build creates a YOLO dataset from labeled MDetect source images and LabelBox coordinates, then optionally expands the dataset to a target image count per class.

The Step 15 target classes are:

- soap_case_pink
- soap_case_white
- soap_case_mint
- shampoo_case_white
- other

This feature is optional. When `Use augmentation` is off, the existing Dataset Build flow remains unchanged.

## Why This Exists

The current labeled set can start with class별 5 images, total 25 images. Augmentation can produce a larger training dataset, such as class별 500 images, by transforming images and bounding boxes together.

This does not replace real data collection. Five original images expanded to 500 samples can still overfit because all generated samples inherit the same few object poses, backgrounds, lighting patterns, and camera conditions.

Recommended strategy:

- MVP: 50 original images per class with moderate augmentation.
- Better baseline: 50 original images/class x 10x augmentation.
- More stable: 100 to 300 original images per class before heavy training.

## Dataset Flow

1. Select labeled source images.
2. Split source images into train/val/test first.
3. Copy original images and labels into the selected split.
4. Generate augmented images within the same split as the source image.
5. Transform bounding boxes with the same scale/shift operation.
6. Clip boxes to image boundaries.
7. Skip augmented samples where boxes become invalid or too small.
8. Write YOLO labels and `data.yaml`.

The source-image-first split prevents leakage where augmented copies of the same original image appear across train/val/test.

## Implemented Augmentations

Step 15 implements these color-safe augmentations:

- brightness: 0.85 to 1.15
- contrast: 0.85 to 1.15
- blur: low probability
- noise: low probability
- horizontal shift: up to +/- 5% of image width
- vertical shift: up to +/- 5% of image height
- scale: 0.9 to 1.1

## Deferred Augmentations

These are intentionally deferred:

- rotation
- perspective
- hue shift
- saturation shift

Rotation and perspective require more careful geometric box conversion. Hue and saturation changes are avoided because this project separates classes by color and product type.

## Color-Safe Policy

Color-safe augmentation avoids transforms that can move one class visually toward another class.

Avoid:

- pink becoming white
- mint becoming white
- white becoming mint
- strong hue changes
- strong saturation changes

Allowed:

- weak brightness
- weak contrast
- weak blur
- weak noise
- weak shift
- weak scale

## Bounding Box Conversion

For scale and shift, each box is transformed by:

```text
x' = x * scale + offset_x
y' = y * scale + offset_y
```

Then the box is clipped to the image boundary. Invalid or tiny boxes are skipped.

Original `LabelBox` records are never modified. Augmented boxes are written only to YOLO label files.

## Class Target Count

`Target images per class` includes originals.

Example:

- original source images for `soap_case_pink`: 5
- target images per class: 500
- generated augmented images needed: about 495

Generation is capped by `Max augmentations per source image`.

## Warnings

Augmented Dataset Build records and displays warnings when:

- source images per class are fewer than 10
- target count is at least 50x source count
- `other` has fewer than 10 source images
- `soap_case_white` / `soap_case_mint` source data is low
- `soap_case_white` / `shampoo_case_white` source data is low

Warnings do not block a build.

## Existing Feature Impact

No DB schema change is required. Augmentation options are stored in `DatasetVersion.build_config_json`.

Existing Dataset Build behavior remains the default when `Use augmentation` is unchecked.
