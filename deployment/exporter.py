import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import close_old_connections
from django.utils import timezone

from .models import AndroidModelPackage


def yolo_executable():
    configured = getattr(settings, 'MDETECT_EXPORT_YOLO_BIN', '') or os.environ.get('MDETECT_EXPORT_YOLO_BIN', '')
    if configured:
        configured_path = Path(configured).expanduser()
        if configured_path.is_file():
            return str(configured_path)

    executable = shutil.which('yolo')
    if executable:
        return executable

    python_sibling = Path(sys.executable).resolve().parent / 'yolo'
    if python_sibling.is_file():
        return str(python_sibling)

    return None


def yolo_subprocess_env():
    env = os.environ.copy()
    executable = yolo_executable()
    if executable:
        executable_bin = str(Path(executable).resolve().parent)
        env['PATH'] = f'{executable_bin}{os.pathsep}{env.get("PATH", "")}'
        env.setdefault('MDETECT_EXPORT_YOLO_BIN', executable)
    cuda_lib = Path(sys.executable).resolve().parents[1] / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages' / 'nvidia' / 'cu13' / 'lib'
    if cuda_lib.is_dir():
        existing = env.get('LD_LIBRARY_PATH')
        env['LD_LIBRARY_PATH'] = f'{cuda_lib}{os.pathsep}{existing}' if existing else str(cuda_lib)
    return env


def start_export_package(package):
    thread = threading.Thread(target=run_export_package, args=(package.id,), daemon=True)
    thread.start()
    return thread


def package_output_dir(package):
    return Path(settings.PROJECT_DATA_DIR) / 'android_exports' / package.model_version


def class_names_for_package(package):
    names = package.trained_model.class_names_json or []
    if names:
        return names
    return package.trained_model.training_job.dataset_version.class_summary_json.get('class_names', [])


def metadata_for_package(package, classes):
    return {
        'model_version': package.model_version,
        'model_format': 'tflite',
        'task': 'object_detection',
        'input_size': package.input_size,
        'classes': classes,
        'confidence_threshold': package.confidence_threshold,
        'iou_threshold': package.iou_threshold,
        'created_at': package.created_at.isoformat() if package.created_at else timezone.now().isoformat(),
        'training_job_id': package.trained_model.training_job_id,
        'dataset_version_id': package.trained_model.training_job.dataset_version_id,
        'trained_model_id': package.trained_model_id,
        'metrics': package.trained_model.metrics_json or {},
    }


def write_labels_and_metadata(package):
    output_dir = package_output_dir(package)
    output_dir.mkdir(parents=True, exist_ok=True)
    classes = class_names_for_package(package)
    labels_path = output_dir / 'labels.txt'
    metadata_path = output_dir / 'metadata.json'
    labels_path.write_text('\n'.join(classes) + ('\n' if classes else ''), encoding='utf-8')
    metadata_path.write_text(json.dumps(metadata_for_package(package, classes), indent=2), encoding='utf-8')
    return labels_path, metadata_path


def attach_file(package, field_name, path):
    relative = Path('android_exports') / package.model_version / path.name
    with path.open('rb') as handle:
        getattr(package, field_name).save(str(relative), File(handle), save=False)


def run_export_package(package_id):
    close_old_connections()
    package = AndroidModelPackage.objects.select_related(
        'trained_model__training_job__dataset_version'
    ).get(pk=package_id)
    output_dir = package_output_dir(package)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / 'export_log.txt'
    package.status = AndroidModelPackage.Status.RUNNING
    package.export_log = str(log_path)
    package.save(update_fields=['status', 'export_log'])

    try:
        labels_path, metadata_path = write_labels_and_metadata(package)
        model_path = Path(package.trained_model.model_path)
        if not model_path.exists():
            raise FileNotFoundError(f'Trained model file does not exist: {model_path}')
        yolo_command = yolo_executable()
        command = [yolo_command or 'yolo', 'export', f'model={model_path}', 'format=tflite', f'imgsz={package.input_size}']
        with log_path.open('w', encoding='utf-8') as log:
            log.write(f'export_yolo_bin={yolo_command or "yolo"}\n')
            log.write(f'django_python={sys.executable}\n')
            log.write(f'working_dir={output_dir}\n\n')
            log.write(' '.join(command) + '\n\n')
            if yolo_command is None:
                raise RuntimeError('yolo command is not available in this environment.')
            result = subprocess.run(command, cwd=str(output_dir), stdout=log, stderr=subprocess.STDOUT, text=True, check=False, env=yolo_subprocess_env())
        if result.returncode != 0:
            raise RuntimeError(f'TFLite export exited with code {result.returncode}.')
        tflite_candidates = sorted(output_dir.rglob('*.tflite'))
        if not tflite_candidates:
            tflite_candidates = sorted(model_path.parent.rglob('*.tflite'))
        if not tflite_candidates:
            raise FileNotFoundError('TFLite export completed but no .tflite file was found.')
        tflite_path = output_dir / 'model.tflite'
        if tflite_candidates[0] != tflite_path:
            shutil.copy2(tflite_candidates[0], tflite_path)
        attach_file(package, 'tflite_file', tflite_path)
        attach_file(package, 'labels_file', labels_path)
        attach_file(package, 'metadata_file', metadata_path)
        package.status = AndroidModelPackage.Status.COMPLETED
        package.error_message = ''
        package.save(update_fields=['tflite_file', 'labels_file', 'metadata_file', 'status', 'error_message'])
    except Exception as exc:
        with log_path.open('a', encoding='utf-8') as log:
            log.write(f'\nERROR: {exc}\n')
            log.write('Failed AndroidModelPackage record deleted so model_version can be reused.\n')
        package.delete()
    finally:
        close_old_connections()


def create_fake_completed_package_files(package):
    output_dir = package_output_dir(package)
    output_dir.mkdir(parents=True, exist_ok=True)
    labels_path, metadata_path = write_labels_and_metadata(package)
    tflite_path = output_dir / 'model.tflite'
    tflite_path.write_bytes(b'MDETECT_FAKE_TFLITE')
    attach_file(package, 'tflite_file', tflite_path)
    attach_file(package, 'labels_file', labels_path)
    attach_file(package, 'metadata_file', metadata_path)
    package.status = AndroidModelPackage.Status.COMPLETED
    package.save(update_fields=['tflite_file', 'labels_file', 'metadata_file', 'status'])
