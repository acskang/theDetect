# MDetect Labeling Manual Test Guide

## Preconditions
- Run migrations.
- Create a user and log in.
- Upload at least one image from `/datasets/images/upload/`.
- Ensure active object classes exist: `class_01`, `class_02`, `other`.

## Manual Test
1. Open `/labeling/`.
2. Confirm uploaded images appear with thumbnail, status, hint class, and label count.
3. Open `/labeling/images/<image_id>/`.
4. Select a class.
5. Draw a bounding box over the image.
6. Save boxes.
7. Reload the page and confirm the box appears again.
8. Select the box and delete it.
9. Save boxes again and confirm label count changes.
10. Draw a final box and click Save boxes. Confirm the image status becomes labeled.
11. Use Next image to move to another unlabeled image when available.

## Save API Example
```bash
curl -X POST http://127.0.0.1:8000/labeling/images/1/boxes/save/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <csrf-token>" \
  -b "csrftoken=<csrf-token>; sessionid=<session-id>" \
  -d '{"boxes":[{"object_class_id":1,"x_min":120,"y_min":80,"x_max":420,"y_max":500}]}'
```

Expected response:

```json
{"saved": true, "count": 1}
```
