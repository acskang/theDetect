import os
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.management import call_command
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from datasets.models import DatasetVersion, ObjectClass, UploadedImage
from detection.models import DetectionLog
from detection.services.yolo_inference import (
    InferenceError,
    ImageValidationError,
    run_yolo_inference,
    validate_uploaded_image,
)
from models_registry.models import TrainedModel
from . import manual_services


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
    })


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


@login_required
def manual_home(request):
    stage = request.GET.get('stage') or None
    selected_doc = request.GET.get('doc') or manual_services.first_doc_path(stage)
    if selected_doc:
        url = reverse('core:manual_view', kwargs={'doc_path': selected_doc})
        query = request.GET.urlencode()
        return redirect(f'{url}?{query}' if query else url)
    return render_manual(request, current_doc=None, current_stage=stage)


@login_required
def manual_view(request, doc_path):
    current_doc = manual_services.load_document(doc_path)
    current_stage = request.GET.get('stage') or current_doc.stage
    return render_manual(request, current_doc=current_doc, current_stage=current_stage)


@login_required
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
        'current_stage_files': stage_file_map.get(current_stage, []),
        'current_stage': current_stage,
        'current_doc': current_doc,
        'selected_doc_path': current_doc.relative_path if current_doc else '',
        'search_query': query,
        'search_results': manual_services.search_documents(query, current_stage),
    })


@login_required
def api_test(request):
    return render(request, 'core/api_test.html', {'service_base_url': settings.SERVICE_BASE_URL})


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
