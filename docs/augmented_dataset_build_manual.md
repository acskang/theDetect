# Augmented Dataset Build Manual

## When To Use

Use Augmented Dataset Build when labeled source images are too few for YOLO training and you need a larger dataset for an initial model.

Step 18 moved this workflow to its own screen:

```text
/datasets/build/augmented/
```

The regular Dataset Build screen no longer shows augmentation fields.

For the current color/product classes, augmentation can help start training, but 5 originals per class expanded to 500 images has high overfitting risk.

Recommended data strategy:

- collect at least 50 original images per class
- use about 10x augmentation
- verify with Server Mode before Android deployment

## Screen Options

Open:

```text
Dataset Build
```

Fields:

- Name: DatasetVersion name.
- Description: Optional description.
- Train ratio: default 80.
- Val ratio: default 10.
- Test ratio: default 10.
- Random seed: controls split and augmentation reproducibility.
- Include only labeled images: recommended on.
- Exclude invalid boxes: recommended on.
- Build memo: optional memo.
- Use augmentation: enable Augmented Dataset Build.
- Target images per class: default 500.
- Max augmentations per source image: default 100.
- Color-safe augmentation: default on.

Dataset Versions shows the resulting build type as `augmented`.

## Recommended Settings For Current MVP

If each class has only 5 labeled originals:

```text
Use augmentation: checked
Target images per class: 500
Max augmentations per source image: 100
Color-safe augmentation: checked
```

This can create the requested dataset, but it should be treated as an initial experiment, not a final production dataset.

## Build Output

The output uses the same YOLO folder structure as the normal Dataset Build:

```text
project_data/datasets/<dataset_version>/
├── images/train/
├── images/val/
├── images/test/
├── labels/train/
├── labels/val/
├── labels/test/
└── data.yaml
```

Augmented files include `_augNNNN` in the filename.

## Label Safety

Augmented images do not change the original UploadedImage or LabelBox records.

The builder transforms boxes only for YOLO label export. Boxes that become invalid or too small are skipped.

## Split Leakage Prevention

MDetect first splits original source images into train/val/test. Augmented copies stay in the same split as their source image.

This reduces the risk that near-duplicate images appear in both training and test data.

## After Build

1. Open Dataset Versions and confirm the new version is built.
2. Open Training Jobs.
3. Train a YOLO model with the augmented DatasetVersion.
4. Open Model Registry.
5. Set the trained model active only after checking class names and metrics.
6. Test in Server Mode first.
7. Review Detection Logs for white/mint and soap/shampoo confusion.

## Known Limitation

Implemented in Step 15:

- brightness
- contrast
- blur
- noise
- horizontal shift
- vertical shift
- scale

Not implemented in Step 15:

- rotation
- perspective
- hue shift
- saturation shift

Hue/saturation are intentionally not used for color-separated classes.
