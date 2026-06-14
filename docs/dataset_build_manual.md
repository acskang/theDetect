# MDetect Dataset Build Manual

## URL
Open:

```text
/datasets/build/
```

## Build Options
- Dataset version name
- Description
- Train ratio
- Validation ratio
- Test ratio
- Random seed
- Include only labeled images
- Exclude invalid boxes
- Build memo

The split ratios must add up to 100 and each ratio must be greater than 0.

## Label Conversion
Each `LabelBox` is converted to YOLO format:

```text
class_id x_center y_center width height
```

The normalized values are calculated from original image pixel coordinates:

```text
x_center = ((x_min + x_max) / 2) / image_width
y_center = ((y_min + y_max) / 2) / image_height
width = (x_max - x_min) / image_width
height = (y_max - y_min) / image_height
```

## Class Balance Warnings
Warnings are shown for:
- classes with no labels
- classes with very few labels
- too many `other` labels
- invalid boxes
- many unlabeled images
- split outputs missing labels for a class

Warnings do not block the build.
