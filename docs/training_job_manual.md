# MDetect Training Job Manual

## URLs
- Training Jobs: `/training/jobs/`
- Training Job Detail: `/training/jobs/<job_id>/`
- Model Registry: `/models/registry/`

## Start Training
1. Build a DatasetVersion.
2. Open `/training/jobs/`.
3. Select the built DatasetVersion.
4. Configure base model, image size, epochs, batch size, device, patience, workers, and memo.
5. Submit the form.

The server starts a background thread that runs:

```bash
yolo detect train data=<data.yaml> model=<base_model> imgsz=<imgsz> epochs=<epochs> batch=<batch> device=<device> project=<training_runs_dir> name=<job_name>
```

If `yolo11n.pt` fails, the runner retries once with `yolov8n.pt`.

## Logs and Artifacts
Open the Training Job Detail page to inspect:
- status
- settings
- latest log
- metrics JSON
- artifact path

Logs are written to:

```text
project_data/training_runs/<job_name>/training_log.txt
```

## Model Registry
Completed jobs register a `TrainedModel` when `best.pt` or `last.pt` exists. The Model Registry can mark one model as the active server model for later server-side detection work.

## Not Included
Step 04 does not export Android `.tflite` packages and does not expose Android deployment APIs.
