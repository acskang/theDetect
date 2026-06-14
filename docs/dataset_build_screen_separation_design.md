# Dataset Build Screen Separation Design

## Purpose

Step 18 separates two different workflows that were previously mixed on one Dataset Build screen.

```text
Dataset Build
- builds a YOLO DatasetVersion from original labeled images only
- does not show augmentation options

Augmented Dataset Build
- builds a YOLO DatasetVersion after image and Bounding Box augmentation
- shows augmentation options

Dataset Versions
- lists both original and augmented DatasetVersions
```

## Reason For Separation

The `Use augmentation` checkbox made one screen represent two workflows. This was easy to misunderstand because original build and augmented build have different risks, expected output sizes, and operational meanings.

The separated screens make the user choose the workflow before entering build parameters.

## URL Structure

```text
/datasets/build/            Dataset Build
/datasets/build/augmented/  Augmented Dataset Build
/datasets/versions/         Dataset Versions
```

## Dataset Build

Dataset Build creates a dataset from labeled originals as-is.

Fields:

- Name
- Description
- Train ratio
- Val ratio
- Test ratio
- Random seed
- Include only labeled images
- Exclude invalid boxes
- Build memo

Stored config:

```json
{
  "build_type": "original",
  "use_augmentation": false
}
```

## Augmented Dataset Build

Augmented Dataset Build creates augmented images and transformed YOLO labels in a new DatasetVersion folder. Original UploadedImage and LabelBox records are not modified.

Fields:

- Name
- Description
- Train ratio
- Val ratio
- Test ratio
- Random seed
- Include only labeled images
- Exclude invalid boxes
- Target images per class
- Max augmentations per source image
- Color-safe augmentation
- Build memo

There is no `Use augmentation` checkbox because this screen always runs augmentation.

Stored config:

```json
{
  "build_type": "augmented",
  "use_augmentation": true,
  "target_images_per_class": 500,
  "max_augmentations_per_source_image": 100,
  "color_safe_augmentation": true
}
```

## Dataset Versions Type

Dataset Versions now displays `Type` from `DatasetVersion.build_config_json.build_type`.

Older records without build type display `unknown`.

## Compatibility

- Existing Dataset Build remains available at `/datasets/build/`.
- Existing DatasetVersions remain queryable.
- Training Jobs can use both original and augmented DatasetVersions.
- No DB schema change is required.
- Android code and Server Mode API are not changed.

## Risk Notice

Class별 5 original images to 500 augmented images is suitable for smoke/trial training only. Production accuracy requires more real source images.

Recommended baseline:

```text
class별 원본 50장 이상 x 10배 증강
```
