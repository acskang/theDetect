import time
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from detection.models import DetectionLog
from detection.services.yolo_inference import (
    ImageValidationError,
    InferenceError,
    run_yolo_inference,
    validate_uploaded_image,
)
from models_registry.models import TrainedModel


class Command(BaseCommand):
    help = 'Run a local server-mode YOLO smoke test against the active TrainedModel.'

    def add_arguments(self, parser):
        parser.add_argument('--image', required=True, help='Path to a jpg/jpeg/png/webp image.')
        parser.add_argument('--username', default='', help='Optional username to attach to DetectionLog.')
        parser.add_argument('--device-info', default='management-command-smoke')
        parser.add_argument('--app-version', default='step10-smoke')
        parser.add_argument('--no-log', action='store_true', help='Run inference without creating DetectionLog.')

    def handle(self, *args, **options):
        image_path = Path(options['image'])
        if not image_path.exists() or not image_path.is_file():
            raise CommandError(f'Image file does not exist: {image_path}')

        active_model = TrainedModel.objects.filter(is_active_server_model=True).first()
        if active_model is None:
            self.stdout.write('model_available=false')
            self.stdout.write('message=No active server model is available.')
            return

        started = time.monotonic()
        try:
            with image_path.open('rb') as image_file:
                validated_image = validate_uploaded_image(File(image_file, name=image_path.name))
        except ImageValidationError as exc:
            raise CommandError(f'Invalid image: {exc}') from exc

        try:
            result = run_yolo_inference(active_model, validated_image)
            model_available = True
            message = 'ok'
            detections = result.detections
        except InferenceError as exc:
            model_available = False
            message = str(exc)
            detections = []

        processing_ms = int((time.monotonic() - started) * 1000)
        log_id = None
        if not options['no_log']:
            log_id = self.create_log(
                image_path=image_path,
                model_version=active_model.name,
                detections=detections,
                processing_ms=processing_ms,
                username=options['username'],
                device_info=options['device_info'],
                app_version=options['app_version'],
            )

        self.stdout.write(f'model_available={str(model_available).lower()}')
        self.stdout.write(f'model_version={active_model.name}')
        self.stdout.write(f'processing_time_ms={processing_ms}')
        self.stdout.write(f'image_width={validated_image.width}')
        self.stdout.write(f'image_height={validated_image.height}')
        self.stdout.write(f'detections_count={len(detections)}')
        self.stdout.write(f'log_id={log_id}')
        self.stdout.write(f'message={message}')

    def create_log(self, image_path, model_version, detections, processing_ms, username, device_info, app_version):
        user = None
        if username:
            user = get_user_model().objects.filter(username=username).first()

        top_detection = max(detections, key=lambda item: item.get('confidence', 0), default=None)
        with image_path.open('rb') as image_file:
            log = DetectionLog.objects.create(
                mode=DetectionLog.Mode.SERVER,
                model_version=model_version,
                image=File(image_file, name=image_path.name),
                detections_json=detections,
                top_class=(top_detection or {}).get('class_name', ''),
                top_confidence=(top_detection or {}).get('confidence'),
                processing_time_ms=processing_ms,
                device_info=device_info,
                app_version=app_version,
                user=user,
                review_status=DetectionLog.ReviewStatus.UNKNOWN,
            )
        return log.id
