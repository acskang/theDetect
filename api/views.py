import time

from django.conf import settings
from django.http import FileResponse
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView

from detection.models import DetectionLog
from detection.services.yolo_inference import (
    InferenceError,
    ImageValidationError,
    run_yolo_inference,
    validate_uploaded_image,
)
from deployment.models import AndroidModelPackage
from models_registry.models import TrainedModel
from .serializers import PhoneOrUsernameTokenObtainPairSerializer


class PhoneOrUsernameTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneOrUsernameTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({'status': 'ok', 'service': 'MDetect'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_test(request):
    return Response({
        'status': 'ok',
        'user': {
            'id': request.user.id,
            'username': request.user.get_username(),
            'is_staff': request.user.is_staff,
        },
    })


def deployed_android_package():
    return AndroidModelPackage.objects.filter(
        is_deployed=True,
        status=AndroidModelPackage.Status.COMPLETED,
    ).select_related('trained_model').first()


def package_classes(package):
    metadata = {}
    if package.metadata_file and package.metadata_file.storage.exists(package.metadata_file.name):
        import json
        with package.metadata_file.open('r') as handle:
            metadata = json.load(handle)
    return metadata.get('classes') or package.trained_model.class_names_json or []


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def latest_android_model(request):
    package = deployed_android_package()
    if package is None:
        return Response({'detail': 'No deployed Android model package.'}, status=status.HTTP_404_NOT_FOUND)
    base = request.build_absolute_uri('/').rstrip('/') or settings.SERVICE_BASE_URL.rstrip('/')
    return Response({
        'model_version': package.model_version,
        'input_size': package.input_size,
        'classes': package_classes(package),
        'confidence_threshold': package.confidence_threshold,
        'iou_threshold': package.iou_threshold,
        'files': {
            'model_tflite': f'{base}/api/models/android/latest/model.tflite',
            'labels': f'{base}/api/models/android/latest/labels.txt',
            'metadata': f'{base}/api/models/android/latest/metadata.json',
        },
    })


def package_file_response(package, field_name, download_name, content_type):
    file_field = getattr(package, field_name)
    if not file_field or not file_field.storage.exists(file_field.name):
        from django.http import Http404
        raise Http404(f'{download_name} not found.')
    return FileResponse(file_field.open('rb'), as_attachment=True, filename=download_name, content_type=content_type)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def latest_android_model_file(request, filename):
    package = deployed_android_package()
    if package is None:
        return Response({'detail': 'No deployed Android model package.'}, status=status.HTTP_404_NOT_FOUND)
    file_map = {
        'model.tflite': ('tflite_file', 'application/octet-stream'),
        'labels.txt': ('labels_file', 'text/plain'),
        'metadata.json': ('metadata_file', 'application/json'),
    }
    if filename not in file_map:
        return Response({'detail': 'Unknown model file.'}, status=status.HTTP_404_NOT_FOUND)
    field_name, content_type = file_map[filename]
    return package_file_response(package, field_name, filename, content_type)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def detect_server(request):
    started = time.monotonic()
    image = request.FILES.get('image')
    try:
        validated_image = validate_uploaded_image(image)
    except ImageValidationError as exc:
        return Response({
            'mode': 'server',
            'model_version': None,
            'model_available': False,
            'processing_time_ms': int((time.monotonic() - started) * 1000),
            'image_width': 0,
            'image_height': 0,
            'detections': [],
            'message': str(exc),
            'log_id': None,
        }, status=status.HTTP_400_BAD_REQUEST)

    active_model = TrainedModel.objects.filter(is_active_server_model=True).first()
    if active_model is None:
        return Response({
            'mode': 'server',
            'model_version': None,
            'model_available': False,
            'processing_time_ms': int((time.monotonic() - started) * 1000),
            'image_width': validated_image.width,
            'image_height': validated_image.height,
            'detections': [],
            'message': 'No active server model is available.',
            'log_id': None,
        })

    try:
        inference_result = run_yolo_inference(active_model, validated_image)
        detections = inference_result.detections
        model_available = True
        message = 'ok'
    except InferenceError as exc:
        detections = []
        model_available = False
        message = str(exc)

    processing_ms = int((time.monotonic() - started) * 1000)
    log_id = save_detection_log_safely(
        request=request,
        image=image,
        model_version=active_model.name,
        detections=detections,
        processing_ms=processing_ms,
    )
    return Response({
        'mode': 'server',
        'model_version': active_model.name,
        'model_available': model_available,
        'processing_time_ms': processing_ms,
        'image_width': validated_image.width,
        'image_height': validated_image.height,
        'detections': detections,
        'message': message,
        'log_id': log_id,
    })


def save_detection_log_safely(request, image, model_version, detections, processing_ms):
    top_detection = max(detections, key=lambda item: item.get('confidence', 0), default=None)
    if image:
        try:
            image.seek(0)
        except Exception:
            pass
    try:
        log = DetectionLog.objects.create(
            mode=DetectionLog.Mode.SERVER,
            model_version=model_version or '',
            image=image,
            detections_json=detections,
            top_class=(top_detection or {}).get('class_name', ''),
            top_confidence=(top_detection or {}).get('confidence'),
            processing_time_ms=processing_ms,
            device_info=request.data.get('device_info', ''),
            app_version=request.data.get('app_version', ''),
            user=request.user if request.user.is_authenticated else None,
            review_status=DetectionLog.ReviewStatus.UNKNOWN,
        )
        return log.id
    except Exception:
        return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detection_logs(request):
    try:
        limit = min(max(int(request.GET.get('limit', 20)), 1), 100)
    except ValueError:
        limit = 20
    results = [
        {
            'id': item.id,
            'mode': item.mode,
            'model_version': item.model_version,
            'top_class': item.top_class,
            'top_confidence': item.top_confidence,
            'created_at': item.created_at.isoformat(),
        }
        for item in DetectionLog.objects.order_by('-created_at')[:limit]
    ]
    return Response({'results': results})
