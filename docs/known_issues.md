# MDetect Known Issues

## Server
- Server Mode runs real YOLO inference only when an active `TrainedModel` points to a valid local YOLO model file and Ultralytics is available.
- Server Mode inference is synchronous in the request path; production should add timeout, queueing, and rate limiting.
- The Step 10 smoke model uses pretrained YOLOv8n COCO classes, not the custom `class_01/class_02/other` dataset.
- Detection History is a minimal list API. Filtering, pagination metadata, and detail views are not implemented.
- Training and export jobs use in-process background threads. Production should use durable workers.
- Real TFLite export depends on local Ultralytics/TensorFlow export support.

## Android
- On-device YOLO output decoding is scaffolded but not model-shape complete.
- Server Detection gracefully handles `model_available=false` responses from the server.
- Server Mode real-device testing requires manual phone operation and depends on LAN reachability, firewall rules, and the active smoke model.
- Detection History displays data only from the minimal server API.
- Real-device CameraX and network tests still need manual execution.

## Operations
- The MVP test account must be created via environment variables; server code does not hardcode the password.
- Debug default server URL is `http://10.0.2.2:8000`, which is emulator-specific.

## Color/Product Class Known Issues
- `soap_case_white` and `soap_case_mint` can be confused depending on lighting, exposure, and white balance.
- `soap_case_white` and `shampoo_case_white` can both be white-toned, so color alone is not enough to distinguish them.
- White product separation needs enough images where whole-object shape, aspect ratio, logo, and structure differences are visible.
- Strong hue/saturation augmentation can collapse class boundaries in color class separation training.
- If the `other` class is too large, the model can become biased toward `other`.
- Current On-device Mode has TFLite model loading and fallback structure, but YOLO TFLite output decoding is not complete yet.
## Augmented Dataset Build Known Issues

- Class별 5 original images를 500 images로 증강하는 것은 가능하지만 overfitting risk가 높다.
- Augmentation cannot create truly new camera angles, backgrounds, product variations, or lighting diversity from too few originals.
- Recommended strategy is at least 50 original images per class with about 10x augmentation.
- Step 15 implements brightness, contrast, blur, noise, shift, and scale only.
- Rotation and perspective are deferred because bounding box conversion is more complex.
- Strong hue/saturation augmentation is intentionally not implemented because color is part of the class boundary.
- soap_case_white vs soap_case_mint and soap_case_white vs shampoo_case_white still require real source images with clear shape, logo, and lighting variation.
- DatasetVersions created before Step 18 may not have `build_config_json.build_type`; the list can show them as `unknown`.
