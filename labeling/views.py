import json
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from PIL import Image

from datasets.models import ObjectClass, UploadedImage

from .models import LabelBox
from .services import auto_label_with_active_model, create_rough_boxes, duplicate_previous_boxes


def ensure_image_dimensions(image):
    if image.width and image.height:
        return True
    try:
        with Image.open(image.file.path) as pil_image:
            image.width, image.height = pil_image.size
        image.save(update_fields=['width', 'height', 'updated_at'])
        return True
    except (FileNotFoundError, OSError, ValueError):
        image.status = UploadedImage.Status.INVALID
        image.save(update_fields=['status', 'updated_at'])
        return False


@login_required
def workspace(request):
    status = request.GET.get('status', '')
    object_classes = list(ObjectClass.objects.filter(is_active=True).order_by('sort_order', 'name'))
    selected_class = None
    selected_class_id = request.GET.get('class', '')
    if selected_class_id:
        selected_class = next(
            (object_class for object_class in object_classes if str(object_class.id) == selected_class_id),
            None,
        )

    images = UploadedImage.objects.select_related('hint_class')
    if selected_class is not None:
        images = images.filter(
            Q(hint_class=selected_class) | Q(label_boxes__object_class=selected_class)
        ).distinct()
    images = images.annotate(label_count=Count('label_boxes', distinct=True))
    if status in UploadedImage.Status.values:
        images = images.filter(status=status)

    class_tabs = []
    for object_class in object_classes:
        count = (
            UploadedImage.objects
            .filter(Q(hint_class=object_class) | Q(label_boxes__object_class=object_class))
            .distinct()
            .count()
        )
        class_tabs.append({'object_class': object_class, 'count': count})

    context = {
        'images': images[:200],
        'current_status': status,
        'selected_class': selected_class,
        'status_choices': UploadedImage.Status.choices,
        'object_classes': object_classes,
        'class_tabs': class_tabs,
    }
    return render(request, 'labeling/workspace.html', context)


def workspace_redirect(scope_class_id='', status=''):
    query = {}
    if scope_class_id:
        query['class'] = scope_class_id
    if status:
        query['status'] = status
    url = reverse('labeling:workspace')
    if query:
        url = f'{url}?{urlencode(query)}'
    return redirect(url)


def scope_class_from_post(request):
    scope_class_id = request.POST.get('scope_class_id')
    if not scope_class_id:
        return None
    return get_object_or_404(ObjectClass, pk=scope_class_id, is_active=True)


def add_summary_messages(request, prefix, summary):
    if summary.images_changed:
        messages.success(
            request,
            f'{prefix}: changed {summary.images_changed} image(s), created {summary.boxes_created} box(es).',
        )
    else:
        messages.warning(request, f'{prefix}: no boxes created.')
    for error in summary.errors[:5]:
        messages.warning(request, error)


@login_required
@require_POST
def auto_rough_boxes(request):
    object_class = get_object_or_404(ObjectClass, pk=request.POST.get('object_class_id'), is_active=True)
    scope_class = scope_class_from_post(request)
    summary = create_rough_boxes(object_class=object_class, user=request.user, scope_class=scope_class)
    add_summary_messages(request, 'Auto rough boxes', summary)
    return workspace_redirect(request.POST.get('scope_class_id'), request.POST.get('status'))


@login_required
@require_POST
def duplicate_previous(request):
    scope_class = scope_class_from_post(request)
    summary = duplicate_previous_boxes(user=request.user, scope_class=scope_class)
    add_summary_messages(request, 'Duplicate previous boxes', summary)
    return workspace_redirect(request.POST.get('scope_class_id'), request.POST.get('status'))


@login_required
@require_POST
def auto_label_active_model(request):
    try:
        confidence = float(request.POST.get('confidence', '0.35'))
    except ValueError:
        confidence = 0.35
    scope_class = scope_class_from_post(request)
    summary = auto_label_with_active_model(user=request.user, confidence=confidence, scope_class=scope_class)
    add_summary_messages(request, 'Auto label with active model', summary)
    return workspace_redirect(request.POST.get('scope_class_id'), request.POST.get('status'))


@login_required
def editor(request, image_id):
    image = get_object_or_404(UploadedImage.objects.select_related('hint_class'), pk=image_id)
    if not ensure_image_dimensions(image):
        messages.error(request, 'Image dimensions could not be read. The image was marked invalid.')
        return redirect('labeling:workspace')

    if image.status == UploadedImage.Status.UPLOADED:
        image.status = UploadedImage.Status.LABELING
        image.save(update_fields=['status', 'updated_at'])

    object_classes = list(ObjectClass.objects.filter(is_active=True).order_by('sort_order', 'name'))
    selected_class = None
    selected_class_id = request.GET.get('class', '')
    if selected_class_id:
        selected_class = next(
            (object_class for object_class in object_classes if str(object_class.id) == selected_class_id),
            None,
        )
    workspace_query = {}
    if selected_class is not None:
        workspace_query['class'] = selected_class.id
    status = request.GET.get('status', '')
    if status in UploadedImage.Status.values:
        workspace_query['status'] = status
    workspace_query_string = urlencode(workspace_query)
    boxes = [
        {
            'id': box.id,
            'object_class_id': box.object_class_id,
            'class_name': box.object_class.display_name,
            'color': box.object_class.color,
            'x_min': box.x_min,
            'y_min': box.y_min,
            'x_max': box.x_max,
            'y_max': box.y_max,
        }
        for box in image.label_boxes.select_related('object_class')
    ]
    context = {
        'image': image,
        'object_classes': object_classes,
        'selected_class': selected_class,
        'workspace_query_string': workspace_query_string,
        'boxes_json': boxes,
        'classes_json': [
            {'id': obj.id, 'name': obj.display_name, 'color': obj.color}
            for obj in object_classes
        ],
    }
    return render(request, 'labeling/editor.html', context)


def validate_box_payload(raw_box, image, active_class_ids):
    try:
        object_class_id = int(raw_box['object_class_id'])
        x_min = round(float(raw_box['x_min']))
        y_min = round(float(raw_box['y_min']))
        x_max = round(float(raw_box['x_max']))
        y_max = round(float(raw_box['y_max']))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError('Each box requires object_class_id and numeric coordinates.') from exc

    if object_class_id not in active_class_ids:
        raise ValidationError('Object class is missing or inactive.')
    if x_min < 0 or y_min < 0:
        raise ValidationError('Coordinates cannot be negative.')
    if x_max > image.width or y_max > image.height:
        raise ValidationError('Coordinates cannot exceed the original image size.')
    if x_min >= x_max or y_min >= y_max:
        raise ValidationError('Box max coordinates must be greater than min coordinates.')

    return {
        'object_class_id': object_class_id,
        'x_min': x_min,
        'y_min': y_min,
        'x_max': x_max,
        'y_max': y_max,
        'image_width': image.width,
        'image_height': image.height,
    }


@login_required
@require_POST
def save_boxes(request, image_id):
    image = get_object_or_404(UploadedImage, pk=image_id)
    if not ensure_image_dimensions(image):
        return JsonResponse({'saved': False, 'errors': ['Image dimensions could not be read.']}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'saved': False, 'errors': ['Invalid JSON payload.']}, status=400)

    raw_boxes = payload.get('boxes', [])
    if not isinstance(raw_boxes, list):
        return JsonResponse({'saved': False, 'errors': ['boxes must be a list.']}, status=400)

    active_class_ids = set(ObjectClass.objects.filter(is_active=True).values_list('id', flat=True))
    cleaned_boxes = []
    errors = []
    for index, raw_box in enumerate(raw_boxes):
        try:
            cleaned_boxes.append(validate_box_payload(raw_box, image, active_class_ids))
        except ValidationError as exc:
            errors.append(f'Box {index + 1}: {"; ".join(exc.messages)}')

    if errors:
        return JsonResponse({'saved': False, 'errors': errors}, status=400)

    with transaction.atomic():
        image.label_boxes.all().delete()
        LabelBox.objects.bulk_create([
            LabelBox(image=image, created_by=request.user, **box)
            for box in cleaned_boxes
        ])
        image.status = UploadedImage.Status.LABELED if cleaned_boxes else UploadedImage.Status.UPLOADED
        image.save(update_fields=['status', 'updated_at'])

    return JsonResponse({'saved': True, 'count': len(cleaned_boxes)})


@login_required
@require_POST
def complete_image(request, image_id):
    image = get_object_or_404(UploadedImage, pk=image_id)
    image.status = UploadedImage.Status.LABELED
    image.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Image marked labeled.')
    return redirect('labeling:editor', image_id=image.id)


@login_required
def next_image(request, image_id):
    candidates = UploadedImage.objects.exclude(
        status__in=[UploadedImage.Status.LABELED, UploadedImage.Status.INVALID, UploadedImage.Status.EXCLUDED]
    )
    selected_class = None
    selected_class_id = request.GET.get('class', '')
    if selected_class_id:
        selected_class = ObjectClass.objects.filter(pk=selected_class_id, is_active=True).first()
    if selected_class is not None:
        candidates = candidates.filter(Q(hint_class=selected_class) | Q(label_boxes__object_class=selected_class)).distinct()
    workspace_query = {}
    if selected_class is not None:
        workspace_query['class'] = selected_class.id
    status = request.GET.get('status', '')
    if status in UploadedImage.Status.values:
        workspace_query['status'] = status
        candidates = candidates.filter(status=status)
    query_string = urlencode(workspace_query)

    next_target = candidates.filter(id__gt=image_id).order_by('id').first()
    if next_target is None:
        next_target = candidates.order_by('id').first()
    if next_target is None:
        messages.info(request, 'No remaining images to label.')
        return workspace_redirect(workspace_query.get('class', ''), workspace_query.get('status', ''))
    url = reverse('labeling:editor', kwargs={'image_id': next_target.id})
    if query_string:
        url = f'{url}?{query_string}'
    return redirect(url)
