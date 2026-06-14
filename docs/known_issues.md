# MDetect Known Issues

## Server
- Server Mode runs real YOLO inference only when an active `TrainedModel` points to a valid local YOLO model file and Ultralytics is available.
- Server Mode inference is synchronous in the request path; production should add timeout, queueing, and rate limiting.
- The Step 10 smoke model uses pretrained YOLOv8n COCO classes, not the custom `class_01/class_02/other` dataset.
- Detection History is a minimal list API. Filtering, pagination metadata, and detail views are not implemented.
- Training and export jobs use in-process background threads. Production should use durable workers.
- Real TFLite export depends on local Ultralytics/TensorFlow export support.

## Android
- Step 22 adds signup/login/session restore, but biometric unlock and secure hardware-backed token storage are not implemented yet.
- Step 23 real-device auth validation still requires manual phone execution; server smoke passed but physical restart/session-restore behavior must be observed on the phone.
- Step 25 adds server logout, refresh-token blacklist, and device-token revoke. Keystore-backed encrypted token storage is still not implemented.
- Android stores app auth tokens in DataStore. A later hardening step should evaluate EncryptedDataStore or Keystore-backed storage.
- On-device YOLO TFLite decoding supports first-pass raw single-output YOLO shapes only: `[1, channels, boxes]` and `[1, boxes, channels]`.
- Multi-output TFLite models or built-in-NMS export variants are not decoded yet.
- On-device detection quality still needs validation against the actual exported project model on a real Android device.
- Step 20 exposes On-device tensor shape, decoder layout, local file state, and last error for validation, but it does not harden the decoder for newly observed shapes.
- Server Detection gracefully handles `model_available=false` responses from the server.
- Server Mode real-device testing requires manual phone operation and depends on LAN reachability, firewall rules, and the active smoke model.
- Detection History displays data only from the minimal server API.
- Real-device CameraX and network tests still need manual execution.

## Operations
- New mobile users remain `pending` until an administrator approves their `AccountProfile`.
- Phone number is member information only. Device verification uses `refresh_token + device_token`, not Android phone-number reads.
- The MVP test account must be created via environment variables; server code does not hardcode the password.
- Debug default server URL is `http://10.0.2.2:8000`, which is emulator-specific.

## Color/Product Class Known Issues
- `soap_case_white` and `soap_case_mint` can be confused depending on lighting, exposure, and white balance.
- `soap_case_white` and `shampoo_case_white` can both be white-toned, so color alone is not enough to distinguish them.
- White product separation needs enough images where whole-object shape, aspect ratio, logo, and structure differences are visible.
- Strong hue/saturation augmentation can collapse class boundaries in color class separation training.
- If the `other` class is too large, the model can become biased toward `other`.
- Current On-device Mode has first-pass YOLO TFLite preprocessing and raw output decoding, but real-device validation and model-shape hardening are still required.
## Augmented Dataset Build Known Issues

- Class별 5 original images를 500 images로 증강하는 것은 가능하지만 overfitting risk가 높다.
- Augmentation cannot create truly new camera angles, backgrounds, product variations, or lighting diversity from too few originals.
- Recommended strategy is at least 50 original images per class with about 10x augmentation.
- Step 15 implements brightness, contrast, blur, noise, shift, and scale only.
- Rotation and perspective are deferred because bounding box conversion is more complex.
- Strong hue/saturation augmentation is intentionally not implemented because color is part of the class boundary.
- soap_case_white vs soap_case_mint and soap_case_white vs shampoo_case_white still require real source images with clear shape, logo, and lighting variation.
- DatasetVersions created before Step 18 may not have `build_config_json.build_type`; the list can show them as `unknown`.
