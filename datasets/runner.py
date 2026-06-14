import shutil
import threading
from pathlib import Path
from types import SimpleNamespace

from django.db import close_old_connections
from django.utils import timezone

from .models import DatasetVersion
from .yolo_builder import build_augmented_dataset_version


def start_augmented_dataset_build(dataset_version):
    thread = threading.Thread(target=run_augmented_dataset_build, args=(dataset_version.id,), daemon=True)
    thread.start()
    return thread


def run_augmented_dataset_build(dataset_version_id):
    close_old_connections()
    try:
        dataset = DatasetVersion.objects.select_related('created_by').get(pk=dataset_version_id)
        form = SimpleNamespace(cleaned_data=cleaned_data_from_dataset(dataset))
        build_augmented_dataset_version(form, user=dataset.created_by, dataset=dataset)
    except Exception as exc:
        fail_dataset_build(dataset_version_id, exc)
    finally:
        close_old_connections()


def cleaned_data_from_dataset(dataset):
    config = dataset.build_config_json
    return {
        'name': dataset.name,
        'description': dataset.description,
        'train_ratio': dataset.train_ratio,
        'val_ratio': dataset.val_ratio,
        'test_ratio': dataset.test_ratio,
        'random_seed': dataset.random_seed,
        'include_only_labeled_images': config.get('include_only_labeled_images', True),
        'exclude_invalid_boxes': config.get('exclude_invalid_boxes', True),
        'build_memo': config.get('build_memo', ''),
        'target_images_per_class': config.get('target_images_per_class') or 500,
        'max_augmentations_per_source_image': config.get('max_augmentations_per_source_image') or 0,
        'color_safe_augmentation': config.get('color_safe_augmentation', True),
    }


def fail_dataset_build(dataset_version_id, exc):
    try:
        dataset = DatasetVersion.objects.get(pk=dataset_version_id)
    except DatasetVersion.DoesNotExist:
        return

    output_path = Path(dataset.output_path) if dataset.output_path else None
    if output_path and output_path.exists():
        shutil.rmtree(output_path)

    summary = dict(dataset.class_summary_json or {})
    warnings = list(summary.get('warnings', []))
    warnings.append(f'Background augmented build failed at {timezone.now().isoformat()}: {exc}')
    summary['warnings'] = warnings
    summary['error_message'] = str(exc)
    dataset.class_summary_json = summary
    dataset.status = DatasetVersion.Status.FAILED
    dataset.save(update_fields=['class_summary_json', 'status'])
