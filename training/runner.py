import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from models_registry.models import TrainedModel

from .models import TrainingJob


def yolo_executable():
    executable = shutil.which('yolo')
    if executable:
        return executable

    python_sibling = Path(sys.executable).resolve().parent / 'yolo'
    if python_sibling.is_file():
        return str(python_sibling)

    return None


def yolo_available():
    return yolo_executable() is not None


def yolo_subprocess_env():
    env = os.environ.copy()
    cuda_lib = Path(sys.executable).resolve().parents[1] / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages' / 'nvidia' / 'cu13' / 'lib'
    if cuda_lib.is_dir():
        existing = env.get('LD_LIBRARY_PATH')
        env['LD_LIBRARY_PATH'] = f'{cuda_lib}{os.pathsep}{existing}' if existing else str(cuda_lib)
    return env


def start_training_job(job):
    thread = threading.Thread(target=run_training_job, args=(job.id,), daemon=True)
    thread.start()
    return thread


def run_training_job(job_id):
    close_old_connections()
    job = TrainingJob.objects.select_related('dataset_version').get(pk=job_id)
    run_dir = Path(settings.PROJECT_DATA_DIR) / 'training_runs' / job.name
    run_dir.mkdir(parents=True, exist_ok=True)
    log_file = run_dir / 'training_log.txt'
    config_file = run_dir / 'training_config.json'
    job.status = TrainingJob.Status.RUNNING
    job.started_at = timezone.now()
    job.log_file = str(log_file)
    job.artifacts_path = str(run_dir)
    job.save(update_fields=['status', 'started_at', 'log_file', 'artifacts_path'])

    data_yaml = Path(job.dataset_version.class_summary_json.get('data_yaml') or Path(job.dataset_version.output_path) / 'data.yaml')
    command = training_command(job, data_yaml, job.base_model)
    config_file.write_text(json.dumps({'command': command}, indent=2), encoding='utf-8')

    try:
        result = run_command_with_log(command, log_file)
        if result.returncode != 0 and job.base_model == 'yolo11n.pt':
            fallback_command = training_command(job, data_yaml, 'yolov8n.pt')
            with log_file.open('a', encoding='utf-8') as log:
                log.write('\nPrimary model failed; retrying with yolov8n.pt.\n')
            result = run_command_with_log(fallback_command, log_file)
            config_file.write_text(json.dumps({'command': command, 'fallback_command': fallback_command}, indent=2), encoding='utf-8')
        if result.returncode != 0:
            raise RuntimeError(f'YOLO training exited with code {result.returncode}.')

        weights_dir = run_dir / 'weights'
        best_model = weights_dir / 'best.pt'
        last_model = weights_dir / 'last.pt'
        metrics = collect_metrics(run_dir)
        job.status = TrainingJob.Status.COMPLETED
        job.finished_at = timezone.now()
        job.metrics_json = metrics
        job.save(update_fields=['status', 'finished_at', 'metrics_json'])
        model_path = best_model if best_model.exists() else last_model
        if model_path.exists():
            TrainedModel.objects.update_or_create(
                training_job=job,
                defaults={
                    'name': job.name,
                    'model_path': str(model_path),
                    'model_format': 'pt',
                    'class_names_json': job.dataset_version.class_summary_json.get('class_names', []),
                    'metrics_json': metrics,
                },
            )
    except Exception as exc:
        job.status = TrainingJob.Status.FAILED
        job.finished_at = timezone.now()
        job.error_message = str(exc)
        job.save(update_fields=['status', 'finished_at', 'error_message'])
        with log_file.open('a', encoding='utf-8') as log:
            log.write(f'\nERROR: {exc}\n')
    finally:
        close_old_connections()


def training_command(job, data_yaml, model_name):
    command = [
        yolo_executable() or 'yolo',
        'detect',
        'train',
        f'data={data_yaml}',
        f'model={model_name}',
        f'imgsz={job.imgsz}',
        f'epochs={job.epochs}',
        f'batch={job.batch}',
        f'device={job.device}',
        f'patience={job.patience}',
        f'project={Path(settings.PROJECT_DATA_DIR) / "training_runs"}',
        f'name={job.name}',
        'exist_ok=True',
    ]
    if job.workers != 'auto':
        command.append(f'workers={job.workers}')
    return command


def run_command_with_log(command, log_file):
    with log_file.open('a', encoding='utf-8') as log:
        log.write(' '.join(command) + '\n\n')
        if not yolo_available():
            raise RuntimeError('yolo command is not available in this environment.')
        return subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, text=True, check=False, env=yolo_subprocess_env())


def collect_metrics(run_dir):
    metrics = {}
    results_csv = run_dir / 'results.csv'
    if results_csv.exists():
        metrics['results_csv'] = str(results_csv)
    for name in ['confusion_matrix.png', 'PR_curve.png', 'F1_curve.png', 'labels.jpg']:
        path = run_dir / name
        if path.exists():
            metrics[name] = str(path)
    metrics_file = run_dir / 'metrics.json'
    metrics_file.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    metrics['metrics_json'] = str(metrics_file)
    return metrics
