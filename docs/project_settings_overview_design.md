# Project Settings Overview Design

## Purpose

Step 21 implements Project Settings as a read-only system settings and runtime status dashboard.

The screen is intentionally not an editable settings form. Current theDetect behavior still depends on Django settings, existing model registry rows, deployed Android package rows, and code-level defaults. Showing those values first gives operators a reliable overview without introducing a new settings model or migration.

## URL

```text
/project-settings/
```

The existing sidebar Project Settings menu links to this URL.

## Sections

- Project / Service
- Upload / Image Policy
- Dataset Build Defaults
- Augmented Dataset Build Defaults
- Training Defaults
- Active Server Model
- Deployed Android Model Package
- Android App Integration
- Data Summary
- System Checks

## Value Sources

- Service/runtime values: `theDetect/settings.py`
- Dataset defaults: current Dataset Build implementation defaults
- Augmentation defaults: current augmented dataset build implementation and operating guide
- Training defaults: `training.models.TrainingJob` defaults and runner behavior
- Active server model: `models_registry.TrainedModel.is_active_server_model=True`
- Deployed Android package: `deployment.AndroidModelPackage.is_deployed=True`
- Android integration: Android build config and API URL conventions
- Data summary: counts from `datasets`, `labeling`, `training`, `models_registry`, `deployment`, and `detection`
- System checks: lightweight read-only checks derived from DB state and file existence

## Why Read-only

- No DB schema change is needed for an overview screen.
- Existing training, dataset build, Android export, and API behavior remain untouched.
- Operators can see missing models, package files, invalid boxes, and data counts before changing workflows.
- Editable settings should be added only after deciding which values must be centralized in DB-backed configuration.

## Future Extension

Later steps can add a dedicated editable settings model for selected operational defaults, for example upload size, dataset split defaults, training defaults, and Android deployment policy. That should be a separate migration-backed step with validation, audit expectations, and tests.
