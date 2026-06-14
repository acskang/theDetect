# MDetect Color/Product Class Training Design

## 1. Purpose

This document defines the labeling and training policy for detecting visually similar objects as separate classes in MDetect when the objects differ by color or product type.

Target classes:

```text
soap_case_pink
soap_case_white
soap_case_mint
shampoo_case_white
other
```

Important:

```text
This is a training, labeling, and operations policy document.
It does not affect the current server code, Android code, or DB schema.
```

## 2. Class Definitions

| Class name | Meaning |
| --- | --- |
| `soap_case_pink` | Pink soap case |
| `soap_case_white` | White soap case |
| `soap_case_mint` | Mint or light-sky-blue soap case |
| `shampoo_case_white` | White shampoo case |
| `other` | Objects other than the four target objects above |

Rules:

- Use only lowercase English letters and underscores in class names.
- Keep display name and model class name identical when possible.
- Do not use spaces, Korean text, or special characters in class names.
- An administrator creates real ObjectClass records manually from the Object Classes screen.
- This documentation step does not auto-create ObjectClass records.

## 3. Why Color/Product Class Separation Is Feasible

YOLO object detection models can learn multiple visual signals together:

- shape
- contour
- size
- aspect ratio
- color
- brightness
- texture
- text/logo
- product structure
- background contrast

Therefore, two kinds of separation are feasible:

1. The same product with different colors can be split into different classes.
   Example: `soap_case_pink` / `soap_case_white` / `soap_case_mint`

2. Different product types with identical or similar colors can be split into different classes.
   Example: `soap_case_white` / `shampoo_case_white`

## 4. Operating Principles That Do Not Affect Existing Implementation

This color/product class separation policy is a data operations policy used on top of the existing MDetect features.

To avoid affecting existing functionality, follow these principles:

- Do not automatically delete or modify existing ObjectClass records.
- Do not automatically change existing UploadedImage, LabelBox, DatasetVersion, TrainingJob, or TrainedModel records.
- New classes are explicitly created by an administrator in the Object Classes screen.
- Existing trained models remain unchanged.
- New color/product class training is performed with a new DatasetVersion and a new TrainingJob.
- The existing active server model is not changed until an administrator explicitly clicks Set active.
- The Android deployed model is not changed until an administrator explicitly clicks Set deployed.

## 5. Major Risks

Key risk factors:

- lighting changes
- camera white balance
- overexposure
- shadows
- background reflection
- smartphone model differences
- confusion between white and mint
- confusion between white soap cases and white shampoo cases
- excessive color augmentation
- class data imbalance
- `other` class over-bias

High-risk confusion pairs:

```text
soap_case_white vs soap_case_mint
soap_case_white vs shampoo_case_white
```

## 6. Data Collection Guide

Recommended image count per class:

```text
MVP minimum: at least 50 images per class
Recommended: at least 100-200 images per class
Stabilized model: at least 300 images per class
other: include objects similar to or confusable with each target class
```

Capture conditions:

- bright lighting
- dark lighting
- shadows
- front view
- side view
- top angle
- close distance
- far distance
- varied backgrounds
- varied smartphones
- slightly blurry photos
- slightly tilted photos
- angles that distinguish similar white products
- angles where logos/text are visible
- angles where product shape differences are clear

## 7. Labeling Policy

When labeling in the MDetect Labeling Workspace:

- Draw the Bounding Box around the whole object.
- Do not draw boxes around only logos, text, or color patches.
- Select the exact class that matches both color and product type.
- If multiple objects are visible in one image, label each object with a separate box.
- Do not force-label ambiguous color or product type cases; keep them for separate review.

Examples:

```text
Whole pink soap case box -> soap_case_pink
Whole white soap case box -> soap_case_white
Whole mint soap case box -> soap_case_mint
Whole white shampoo case box -> shampoo_case_white
Other object or non-target product -> other
```

Important:

```text
soap_case_white and shampoo_case_white may both be white.
Label images so that the full product shape, aspect ratio, structure, and logo differences are visible.
```

## 8. Dataset Build Policy

- Do not modify an existing DatasetVersion for new color/product class experiments.
- Create a new DatasetVersion.
- Use the default train/val/test ratio of 80/10/10.
- Confirm every class appears in each split.
- Check build warnings when a class has too few images.
- If the `other` class is too large, the model may become biased toward `other`.
- Keep the data count balanced across classes as much as possible.
- Collect enough separate data for both `soap_case_white` and `shampoo_case_white`.

## 9. Augmentation Policy

Color separation and white-product distinction are core goals, so augmentation must be controlled carefully.

Allowed or recommended:

- weak rotation
- weak translation
- weak scale
- weak blur
- weak noise
- weak brightness/contrast change
- weak perspective change

Use caution or avoid:

- strong hue change
- strong saturation change
- augmentation that changes an object color into another class color
- transformations that make pink look white or mint look white
- transformations that over-brighten white products and erase shape differences

## 10. Training and Evaluation Criteria

Check these after Training Jobs complete:

- confusion matrix
- precision per class
- recall per class
- whether `soap_case_white` is confused with `soap_case_mint`
- whether `soap_case_white` is confused with `shampoo_case_white`
- low-confidence detections
- DetectionLog review
- real Android Server Mode test results

Success criteria:

```text
Each class is detected independently.
white/mint confusion is within an acceptable range.
soap_case_white and shampoo_case_white are distinguished from each other.
other objects are not falsely detected as target classes.
Real-device camera testing returns model_available=true and saves DetectionLog records.
```

## 11. Recommended Operating Flow

1. Confirm `soap_case_pink` / `soap_case_white` / `soap_case_mint` / `shampoo_case_white` / `other` exist in the Object Classes screen.
2. If a class is missing, an administrator creates it manually.
3. Upload images by class.
4. Label the full object Bounding Box in the Labeling Workspace.
5. Run Dataset Build.
6. Run Training Jobs.
7. Confirm the trained model in Model Registry.
8. Use Set active for Server Mode validation.
9. Validate with Android Server Mode on a real device.
10. Run Android Model Export after validation succeeds.
11. Set Model Deployment.
12. Download through Android Model Update.
13. Validate On-device Mode after YOLO TFLite decoding is completed.

## 12. Current Implementation State and Notes

```text
MDetect currently implements real YOLO inference in Server Mode.
On-device Mode has TFLite model loading and fallback structure, but YOLO TFLite output decoding is not complete yet.
Therefore, validate new class models in Server Mode first.
After On-device decoding is completed, validate app-local inference.
```
