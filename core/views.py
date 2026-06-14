import os
import json
import re
import time
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.management import call_command
from django.db import connection
from django.db.models import Count, F, Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from datasets.models import DatasetVersion, ObjectClass, UploadedImage
from deployment.models import AndroidModelPackage
from detection.models import DetectionLog
from detection.services.yolo_inference import (
    InferenceError,
    ImageValidationError,
    run_yolo_inference,
    validate_uploaded_image,
)
from labeling.models import LabelBox
from models_registry.models import TrainedModel
from training.models import TrainingJob
from . import manual_services
from .llama_chat import LlamaChatServiceError, LlamaChatValidationError, build_chat_response


def healthz(request):
    return JsonResponse({'status': 'ok', 'service': settings.SERVICE_NAME})


def readyz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        if os.environ.get('READINESS_CHECK_MIGRATIONS') == '1':
            call_command('showmigrations', '--plan', verbosity=0)
    except Exception as exc:
        return JsonResponse({'status': 'error', 'detail': str(exc)}, status=503)
    return JsonResponse({'status': 'ok', 'service': settings.SERVICE_NAME})


def landing(request):
    return render(request, 'core/landing.html', {
        'service_name': settings.SERVICE_NAME,
        'service_base_url': settings.SERVICE_BASE_URL,
        'login_form': AuthenticationForm(request),
        'chat_widget_enabled': getattr(settings, 'CHAT_WIDGET_ENABLED', True),
    })


@require_POST
def llama_chat(request):
    if not getattr(settings, 'CHAT_WIDGET_ENABLED', True):
        return JsonResponse(
            {'ok': False, 'error': 'AI 채팅 기능이 현재 비활성화되어 있습니다.'},
            status=503,
        )
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON payload.'}, status=400)
    try:
        result = build_chat_response(
            message=body.get('message'),
            history=body.get('history', []),
            page=body.get('page'),
        )
    except LlamaChatValidationError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    except LlamaChatServiceError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=503)
    except Exception:
        return JsonResponse(
            {'ok': False, 'error': '지금은 AI 챗봇 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.'},
            status=503,
        )
    return JsonResponse(result)


@login_required
def dashboard(request):
    """Render the initial MDetect admin dashboard."""
    menu_items = [
        ('Project Settings', 'Step 02 placeholder'),
        ('Object Classes', 'Step 02 placeholder'),
        ('Image Dataset', 'Step 02 placeholder'),
        ('Labeling Workspace', 'Implemented'),
        ('Dataset Build', 'Implemented'),
        ('Training Jobs', 'Implemented'),
        ('Model Registry', 'Implemented'),
        ('Android Model Export', 'Step 05 placeholder'),
        ('Model Deployment', 'Step 05 placeholder'),
        ('Detection Logs', 'Step 02 placeholder'),
        ('Review Queue', 'Step 02 placeholder'),
        ('API Test', 'Step 02 placeholder'),
        ('Manual', 'Implemented'),
    ]
    context = {
        'service_name': settings.SERVICE_NAME,
        'service_base_url': settings.SERVICE_BASE_URL,
        'menu_items': menu_items,
        'stats': {
            'object_classes': ObjectClass.objects.count(),
            'uploaded_images': UploadedImage.objects.count(),
            'dataset_versions': DatasetVersion.objects.count(),
            'detection_logs': DetectionLog.objects.count(),
        },
    }
    return render(request, 'core/dashboard.html', context)


def manual_home(request):
    stage = request.GET.get('stage') or None
    selected_doc = request.GET.get('doc') or manual_services.first_doc_path(stage)
    if selected_doc:
        url = reverse('core:manual_view', kwargs={'doc_path': selected_doc})
        query = request.GET.urlencode()
        return redirect(f'{url}?{query}' if query else url)
    return render_manual(request, current_doc=None, current_stage=stage)


def manual_view(request, doc_path):
    current_doc = manual_services.load_document(doc_path)
    current_stage = request.GET.get('stage') or current_doc.stage
    return render_manual(request, current_doc=current_doc, current_stage=current_stage)


def manual_raw(request, doc_path):
    current_doc = manual_services.load_document(doc_path)
    response = HttpResponse(current_doc.raw_content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'inline; filename="{current_doc.relative_path.rsplit("/", 1)[-1]}"'
    return response


def render_manual(request, current_doc, current_stage=None):
    query = request.GET.get('q', '')
    stage_options = manual_services.build_stage_options()
    stage_file_map = manual_services.build_stage_file_map()
    if not current_stage and stage_options:
        current_stage = stage_options[0]['value']
    stage_groups = [
        {
            'value': stage['value'],
            'label': stage['label'],
            'files': stage_file_map.get(stage['value'], []),
        }
        for stage in stage_options
    ]
    return render(request, 'core/manual.html', {
        'manual_stats': manual_services.manual_stats(),
        'manual_stage_options': stage_options,
        'manual_stage_file_map': stage_file_map,
        'manual_stage_groups': stage_groups,
        'manual_apk_releases': manual_services.latest_apk_releases(),
        'current_stage_files': stage_file_map.get(current_stage, []),
        'current_stage': current_stage,
        'current_doc': current_doc,
        'selected_doc_path': current_doc.relative_path if current_doc else '',
        'search_query': query,
        'search_results': manual_services.search_documents(query, current_stage),
    })


@require_GET
def manual_apk_download(request):
    releases = manual_services.latest_apk_releases(limit=1)
    if not releases:
        return HttpResponse(status=404)
    release = releases[0]
    if not release.path.exists() or not release.path.is_file():
        return HttpResponse(status=404)
    return FileResponse(
        release.path.open('rb'),
        as_attachment=True,
        filename=release.download_filename,
        content_type='application/vnd.android.package-archive',
    )


@login_required
def api_test(request):
    return render(request, 'core/api_test.html', {'service_base_url': settings.SERVICE_BASE_URL})


@login_required
def detection_logs(request):
    mode = request.GET.get('mode', '').strip()
    model_version = request.GET.get('model_version', '').strip()
    logs = DetectionLog.objects.select_related('user').order_by('-created_at')
    if mode:
        logs = logs.filter(mode=mode)
    if model_version:
        logs = logs.filter(model_version__icontains=model_version)
    logs = logs[:100]
    return render(request, 'core/detection_logs.html', {
        'logs': logs,
        'mode': mode,
        'model_version': model_version,
        'total_count': DetectionLog.objects.count(),
        'mode_choices': DetectionLog.Mode.choices,
    })


def _display(value, fallback='-'):
    return fallback if value in (None, '') else value


def _format_bytes(value):
    try:
        size = float(value)
    except (TypeError, ValueError):
        return 'Not configured'
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return f'{size:.0f} {unit}'
        size /= 1024
    return f'{size} B'


def _path_exists(path):
    if not path:
        return False
    try:
        return Path(path).exists()
    except TypeError:
        return False


def _file_field_exists(file_field):
    try:
        return bool(file_field and file_field.name and file_field.storage.exists(file_field.name))
    except Exception:
        return False


def _android_build_value(key, fallback='-'):
    gradle_path = settings.BASE_DIR / 'mobile' / 'MDetect' / 'app' / 'build.gradle.kts'
    try:
        text = gradle_path.read_text(encoding='utf-8')
    except OSError:
        return fallback
    match = re.search(rf'buildConfigField\("String",\s*"{re.escape(key)}",\s*"\\\"([^"]+)\\\""\)', text)
    return match.group(1) if match else fallback


def _check_item(label, ok, detail='', warning=False):
    if ok:
        status = 'OK'
        tone = 'ok'
    elif warning:
        status = 'Warning'
        tone = 'warning'
    else:
        status = 'Missing'
        tone = 'missing'
    return {'label': label, 'status': status, 'tone': tone, 'detail': detail}


@login_required
def project_settings(request):
    active_model = (
        TrainedModel.objects.select_related('training_job', 'training_job__dataset_version')
        .filter(is_active_server_model=True)
        .first()
    )
    active_model_exists = _path_exists(active_model.model_path) if active_model else False

    deployed_package = (
        AndroidModelPackage.objects.select_related('trained_model')
        .filter(is_deployed=True)
        .first()
    )
    deployed_files = {}
    if deployed_package:
        deployed_files = {
            'model.tflite': _file_field_exists(deployed_package.tflite_file),
            'labels.txt': _file_field_exists(deployed_package.labels_file),
            'metadata.json': _file_field_exists(deployed_package.metadata_file),
        }

    object_class_count = ObjectClass.objects.count()
    uploaded_image_count = UploadedImage.objects.count()
    label_box_count = LabelBox.objects.count()
    labeled_image_count = LabelBox.objects.values('image_id').distinct().count()
    invalid_box_count = LabelBox.objects.filter(
        Q(x_min__gte=F('x_max'))
        | Q(y_min__gte=F('y_max'))
        | Q(x_max__gt=F('image_width'))
        | Q(y_max__gt=F('image_height'))
    ).count()
    dataset_version_count = DatasetVersion.objects.count()
    training_job_count = TrainingJob.objects.count()
    trained_model_count = TrainedModel.objects.count()
    android_package_count = AndroidModelPackage.objects.count()
    detection_log_count = DetectionLog.objects.count()

    class_label_stats = (
        LabelBox.objects.values('object_class__name', 'object_class__display_name')
        .annotate(boxes=Count('id'), images=Count('image_id', distinct=True))
        .order_by('object_class__sort_order', 'object_class__name')
    )

    project_data_dir = settings.PROJECT_DATA_DIR
    docs_dir = settings.BASE_DIR / 'docs'

    service = {
        'Service name': 'theDetect',
        'Django service setting': _display(getattr(settings, 'SERVICE_NAME', None), 'Not configured'),
        'Django project name': 'theDetect',
        'Service base URL': _display(getattr(settings, 'SERVICE_BASE_URL', None), 'Not configured'),
        'Environment / DEBUG': 'DEBUG on' if settings.DEBUG else 'DEBUG off',
        'Timezone': _display(getattr(settings, 'TIME_ZONE', None)),
        'Database engine': _display(settings.DATABASES.get('default', {}).get('ENGINE')),
        'Project root': settings.BASE_DIR,
        'Project data directory': project_data_dir,
        'Docs directory': docs_dir,
    }
    upload_policy = {
        'Allowed image extensions': 'jpg, jpeg, png, webp',
        'Allowed ZIP upload': 'Supported',
        'Max upload size': _format_bytes(getattr(settings, 'MDETECT_MAX_UPLOAD_SIZE', None)),
        'Image validation': 'Pillow validation and extension checks',
        'Image max long edge for Android upload': f'{getattr(settings, "MDETECT_MAX_IMAGE_LONG_EDGE", 1280)}px',
    }
    dataset_defaults = {
        'Default train ratio': '80',
        'Default val ratio': '10',
        'Default test ratio': '10',
        'Default random seed': '42',
        'Include only labeled images default': 'true',
        'Exclude invalid boxes default': 'true',
        'Build type': 'original',
    }
    augmentation_defaults = {
        'Target images per class': '500',
        'Max augmentations per source image': '100',
        'Color-safe augmentation': 'true',
        'Implemented augmentation methods': 'brightness, contrast, blur, noise, shift, scale',
        'Disabled / intentionally excluded methods': 'hue shift, saturation shift, rotation, perspective',
        'Overfitting warning': 'class별 원본 5장 -> 500장은 smoke/trial 용도이며 overfitting 위험이 큼',
    }
    training_defaults = {
        'Base model default': 'yolo11n.pt with yolov8n.pt fallback',
        'Image size': '640',
        'Epochs': '50',
        'Batch size': '16',
        'Device': 'auto / configured per job',
        'Patience': '20',
        'Workers': 'auto',
        'Training runner': 'background thread / subprocess',
    }
    android = {
        'Debug base URL': _android_build_value('DEFAULT_SERVER_URL', 'http://10.0.2.2:8000'),
        'Release base URL': _android_build_value('DEFAULT_SERVER_URL', 'https://detect.thesysm.com'),
        'Auth method': 'JWT',
        'Default MVP username': _android_build_value('DEFAULT_USERNAME', 'mdetect_smoke'),
        'Server Mode endpoint': '/api/detect/server/',
        'Model Update endpoint': '/api/models/android/latest/',
        'Detection History endpoint': '/api/detection-logs/',
        'On-device mode status': 'implemented first-pass YOLO TFLite decoder; shape-specific verification required',
    }
    data_summary = {
        'ObjectClass count': object_class_count,
        'UploadedImage count': uploaded_image_count,
        'LabelBox count': label_box_count,
        'DatasetVersion count': dataset_version_count,
        'TrainingJob count': training_job_count,
        'TrainedModel count': trained_model_count,
        'AndroidModelPackage count': android_package_count,
        'DetectionLog count': detection_log_count,
    }
    deployed_files_ok = bool(deployed_files) and all(deployed_files.values())
    system_checks = [
        _check_item('Object classes exist', object_class_count > 0, f'{object_class_count} classes'),
        _check_item('At least one labeled image exists', labeled_image_count > 0, f'{labeled_image_count} labeled images', warning=True),
        _check_item('Invalid boxes count', invalid_box_count == 0, f'{invalid_box_count} invalid boxes', warning=True),
        _check_item('Active server model exists', bool(active_model), active_model.name if active_model else 'No active server model', warning=True),
        _check_item('Active server model file exists', bool(active_model and active_model_exists), active_model.model_path if active_model else '-', warning=True),
        _check_item('Deployed Android package exists', bool(deployed_package), deployed_package.model_version if deployed_package else 'No deployed Android model package', warning=True),
        _check_item('Deployed package files exist', deployed_files_ok, ', '.join(f'{name}: {"yes" if exists else "no"}' for name, exists in deployed_files.items()) if deployed_files else '-', warning=True),
        _check_item('PROJECT_DATA_DIR exists', project_data_dir.exists(), str(project_data_dir), warning=True),
    ]

    return render(request, 'core/project_settings.html', {
        'service_name': settings.SERVICE_NAME,
        'service': service,
        'upload_policy': upload_policy,
        'dataset_defaults': dataset_defaults,
        'augmentation_defaults': augmentation_defaults,
        'training_defaults': training_defaults,
        'active_model': active_model,
        'active_model_file_exists': active_model_exists,
        'active_model_usable_pt': bool(active_model and active_model_exists and Path(active_model.model_path).suffix == '.pt'),
        'deployed_package': deployed_package,
        'deployed_files': deployed_files,
        'android': android,
        'data_summary': data_summary,
        'class_label_stats': class_label_stats,
        'system_checks': system_checks,
    })


@login_required
def server_detection(request):
    active_model = TrainedModel.objects.filter(is_active_server_model=True).first()
    result = None
    error = ''
    log = None

    if request.method == 'POST':
        started = time.monotonic()
        image = request.FILES.get('image')
        try:
            validated_image = validate_uploaded_image(image)
            if active_model is None:
                raise InferenceError('No active server model is available.')
            inference_result = run_yolo_inference(active_model, validated_image)
            processing_ms = int((time.monotonic() - started) * 1000)
            log = create_console_detection_log(
                request=request,
                image=image,
                model_version=active_model.name,
                detections=inference_result.detections,
                processing_ms=processing_ms,
            )
            result = {
                'model_version': active_model.name,
                'processing_time_ms': processing_ms,
                'image_width': inference_result.image_width,
                'image_height': inference_result.image_height,
                'detections': inference_result.detections,
                'log_id': log.id if log else None,
            }
        except (ImageValidationError, InferenceError) as exc:
            error = str(exc)

    return render(request, 'core/server_detection.html', {
        'active_model': active_model,
        'result': result,
        'error': error,
        'log': log,
    })


def create_console_detection_log(request, image, model_version, detections, processing_ms):
    top_detection = max(detections, key=lambda item: item.get('confidence', 0), default=None)
    if image:
        try:
            image.seek(0)
        except Exception:
            pass
    return DetectionLog.objects.create(
        mode=DetectionLog.Mode.SERVER,
        model_version=model_version or '',
        image=image,
        detections_json=detections,
        top_class=(top_detection or {}).get('class_name', ''),
        top_confidence=(top_detection or {}).get('confidence'),
        processing_time_ms=processing_ms,
        device_info='web_console',
        app_version='',
        user=request.user if request.user.is_authenticated else None,
        review_status=DetectionLog.ReviewStatus.UNKNOWN,
    )


@login_required
def placeholder(request, page_name):
    return render(request, 'core/placeholder.html', {'page_name': page_name})
