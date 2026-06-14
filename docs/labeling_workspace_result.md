# MDetect Labeling Workspace Result

## URLs
- Labeling Workspace: `/labeling/`
- Labeling editor: `/labeling/images/<image_id>/`
- Save boxes API: `POST /labeling/images/<image_id>/boxes/save/`
- Next image: `/labeling/images/<image_id>/next/`

## Usage
1. Upload images from Image Dataset.
2. Open Labeling Workspace.
3. Choose an image with Start / edit.
4. Select an active ObjectClass.
5. Drag on the image to create a bounding box.
6. Click a box to select it.
7. Drag the bottom-right handle to resize it.
8. Delete selected box if needed.
9. Save boxes. Saving one or more boxes marks the image labeled.

## Coordinate Storage
The browser editor draws boxes over the displayed image, but converts coordinates to the original image pixel size before saving.

`LabelBox` stores:
- `x_min`
- `y_min`
- `x_max`
- `y_max`
- `image_width`
- `image_height`

These values are the source of truth for Step 04 Dataset Build, where they will be converted to YOLO normalized coordinates.

## Validation
The save API rejects boxes when:
- object class is missing or inactive
- coordinates are negative
- `x_max` exceeds `image_width`
- `y_max` exceeds `image_height`
- `x_min >= x_max`
- `y_min >= y_max`

## Known Limitations
- Box editing supports selection, deletion, and bottom-right resize. Full drag-to-move and multi-handle resize are not implemented.
- Empty box saves are allowed and set the image status back to `uploaded`.
- Dataset Build is not implemented in Step 03.
