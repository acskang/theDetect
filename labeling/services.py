from dataclasses import dataclass

from django.db import transaction

from datasets.models import ObjectClass, UploadedImage
from detection.services.yolo_inference import InferenceError, run_yolo_inference, validate_uploaded_image
from models_registry.models import TrainedModel

from .models import LabelBox


@dataclass
class AutoLabelSummary:
    images_seen: int = 0
    images_changed: int = 0
    boxes_created: int = 0
    skipped: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def empty_label_candidates(scope_class=None):
    candidates = (
        UploadedImage.objects
        .exclude(status__in=[UploadedImage.Status.INVALID, UploadedImage.Status.EXCLUDED])
        .filter(label_boxes__isnull=True)
        .order_by('id')
        .distinct()
    )
    if scope_class is not None:
        candidates = candidates.filter(hint_class=scope_class)
    return candidates


def create_label_box(image, object_class, x_min, y_min, x_max, y_max, user=None):
    return LabelBox.objects.create(
        image=image,
        object_class=object_class,
        x_min=max(0, min(int(round(x_min)), image.width - 1)),
        y_min=max(0, min(int(round(y_min)), image.height - 1)),
        x_max=max(1, min(int(round(x_max)), image.width)),
        y_max=max(1, min(int(round(y_max)), image.height)),
        image_width=image.width,
        image_height=image.height,
        created_by=user if getattr(user, 'is_authenticated', False) else None,
    )


def mark_draft(image):
    image.status = UploadedImage.Status.LABELING
    image.save(update_fields=['status', 'updated_at'])


def create_rough_boxes(object_class, user=None, margin_x_ratio=0.18, margin_y_ratio=0.22, scope_class=None):
    summary = AutoLabelSummary()
    for image in empty_label_candidates(scope_class=scope_class):
        summary.images_seen += 1
        if not image.width or not image.height:
            summary.skipped += 1
            summary.errors.append(f'{image.original_filename}: missing image dimensions.')
            continue
        margin_x = round(image.width * margin_x_ratio)
        margin_y = round(image.height * margin_y_ratio)
        create_label_box(
            image=image,
            object_class=object_class,
            x_min=margin_x,
            y_min=margin_y,
            x_max=image.width - margin_x,
            y_max=image.height - margin_y,
            user=user,
        )
        mark_draft(image)
        summary.images_changed += 1
        summary.boxes_created += 1
    return summary


def duplicate_previous_boxes(user=None, scope_class=None):
    summary = AutoLabelSummary()
    source = (
        UploadedImage.objects
        .filter(label_boxes__isnull=False)
        .exclude(status__in=[UploadedImage.Status.INVALID, UploadedImage.Status.EXCLUDED])
    )
    if scope_class is not None:
        source = source.filter(label_boxes__object_class=scope_class)
    source = source.order_by('-id').distinct().first()
    if source is None:
        summary.errors.append('No source image with boxes exists.')
        return summary

    source_boxes = source.label_boxes.select_related('object_class')
    if scope_class is not None:
        source_boxes = source_boxes.filter(object_class=scope_class)
    source_boxes = list(source_boxes)

    for image in empty_label_candidates(scope_class=scope_class):
        summary.images_seen += 1
        if image.id == source.id:
            summary.skipped += 1
            continue
        if not image.width or not image.height or not source.width or not source.height:
            summary.skipped += 1
            summary.errors.append(f'{image.original_filename}: missing image dimensions.')
            continue

        scale_x = image.width / source.width
        scale_y = image.height / source.height
        for box in source_boxes:
            create_label_box(
                image=image,
                object_class=box.object_class,
                x_min=box.x_min * scale_x,
                y_min=box.y_min * scale_y,
                x_max=box.x_max * scale_x,
                y_max=box.y_max * scale_y,
                user=user,
            )
            summary.boxes_created += 1
        mark_draft(image)
        summary.images_changed += 1
    return summary


def object_class_lookup():
    lookup = {}
    for object_class in ObjectClass.objects.filter(is_active=True):
        lookup[object_class.name.strip().lower()] = object_class
        lookup[object_class.display_name.strip().lower()] = object_class
    return lookup


def auto_label_with_active_model(user=None, confidence=0.35, max_images=200, scope_class=None):
    summary = AutoLabelSummary()
    active_model = TrainedModel.objects.filter(is_active_server_model=True).select_related('training_job').first()
    if active_model is None:
        summary.errors.append('No active server model exists.')
        return summary

    lookup = object_class_lookup()
    for image in empty_label_candidates(scope_class=scope_class)[:max_images]:
        summary.images_seen += 1
        try:
            image.file.open('rb')
            validated = validate_uploaded_image(image.file)
            result = run_yolo_inference(active_model, validated, conf=confidence)
        except (OSError, InferenceError, ValueError) as exc:
            summary.skipped += 1
            summary.errors.append(f'{image.original_filename}: {exc}')
            continue
        finally:
            image.file.close()

        created_for_image = 0
        with transaction.atomic():
            for detection in result.detections:
                object_class = lookup.get(str(detection.get('class_name', '')).strip().lower())
                if object_class is None:
                    continue
                box = detection['box']
                create_label_box(
                    image=image,
                    object_class=object_class,
                    x_min=box['x_min'],
                    y_min=box['y_min'],
                    x_max=box['x_max'],
                    y_max=box['y_max'],
                    user=user,
                )
                created_for_image += 1
        if created_for_image:
            mark_draft(image)
            summary.images_changed += 1
            summary.boxes_created += created_for_image
        else:
            summary.skipped += 1
    return summary
