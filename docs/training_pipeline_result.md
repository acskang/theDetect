# MDetect Training Pipeline Result

## Implemented in Step 04
- Dataset Build UI at `/datasets/build/`.
- DatasetVersion list at `/datasets/versions/`.
- LabelBox to YOLO label conversion.
- train/val/test split output.
- `data.yaml` generation.
- Class balance warnings.
- TrainingJob model and UI at `/training/jobs/`.
- TrainingJob detail at `/training/jobs/<job_id>/`.
- Background YOLO runner with log file output.
- TrainedModel registry at `/models/registry/`.

## YOLO Dataset Output
Dataset builds are written under:

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

## Class ID Mapping
Active ObjectClass records are ordered by:

```text
sort_order, id, name
```

The generated mapping is stored in `DatasetVersion.class_summary_json` so the DatasetVersion keeps a stable class mapping after build.

## Training Output
Training jobs write outputs under:

```text
project_data/training_runs/<job_name>/
```

Expected files include `training_config.json`, `training_log.txt`, YOLO artifacts, and `metrics.json` when available.

## TrainedModel Registration
When YOLO training completes and a `best.pt` or `last.pt` exists, a `TrainedModel` row is registered with:

```text
name
training_job
model_path
model_format=pt
class_names_json
metrics_json
```

## Next Step Use
Step 05 Android Export will use `TrainedModel.model_path` as the source model for export/deployment packaging.

## Known Limitations
- Training cancellation is represented in the model status but no process cancellation UI is implemented.
- Training runs in an in-process background thread for MVP. A production deployment should move this to Celery or another durable worker.
- Android model export and deployment API are not implemented in Step 04.
