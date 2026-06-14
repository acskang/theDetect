from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import AugmentedDatasetBuildForm, DatasetBuildForm, ImageUploadForm, ObjectClassForm
from .models import DatasetVersion, ObjectClass, UploadedImage
from .runner import start_augmented_dataset_build
from .uploading import handle_multi_upload, handle_zip_upload
from .yolo_builder import build_dataset_version, dataset_warnings, prepare_augmented_dataset_version, source_image_counts_by_class


def object_class_list(request):
    object_classes = ObjectClass.objects.all()
    return render(request, 'datasets/object_class_list.html', {'object_classes': object_classes})


def object_class_create(request):
    if request.method == 'POST':
        form = ObjectClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Object class created.')
            return redirect('datasets:object_class_list')
    else:
        form = ObjectClassForm()
    return render(request, 'datasets/object_class_form.html', {'form': form, 'mode': 'Create'})


def object_class_edit(request, pk):
    object_class = get_object_or_404(ObjectClass, pk=pk)
    if request.method == 'POST':
        form = ObjectClassForm(request.POST, instance=object_class)
        if form.is_valid():
            form.save()
            messages.success(request, 'Object class updated.')
            return redirect('datasets:object_class_list')
    else:
        form = ObjectClassForm(instance=object_class)
    return render(request, 'datasets/object_class_form.html', {'form': form, 'mode': 'Edit', 'object_class': object_class})


def image_list_redirect(class_id=''):
    url = reverse('datasets:image_list')
    if class_id:
        url = f'{url}?{urlencode({"class": class_id})}'
    return redirect(url)


def image_list(request):
    object_classes = list(ObjectClass.objects.filter(is_active=True).order_by('sort_order', 'name'))
    selected_class = None
    selected_class_id = request.GET.get('class', '')
    if selected_class_id:
        selected_class = next(
            (object_class for object_class in object_classes if str(object_class.id) == selected_class_id),
            None,
        )

    images = UploadedImage.objects.select_related('hint_class', 'uploaded_by')
    if selected_class is not None:
        images = images.filter(hint_class=selected_class)

    class_tabs = []
    counts = {
        item['hint_class']: item['count']
        for item in UploadedImage.objects.values('hint_class').annotate(count=Count('id'))
    }
    for object_class in object_classes:
        class_tabs.append({
            'object_class': object_class,
            'count': counts.get(object_class.id, 0),
        })

    context = {
        'images': images[:100],
        'object_classes': object_classes,
        'selected_class': selected_class,
        'class_tabs': class_tabs,
        'unassigned_count': counts.get(None, 0),
    }
    return render(request, 'datasets/image_list.html', context)


def image_upload(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            summaries = []
            hint_class = form.cleaned_data.get('object_class')
            image_files = request.FILES.getlist('images')
            if image_files:
                summaries.append(('Images', handle_multi_upload(image_files, uploaded_by=request.user, hint_class=hint_class)))
            zip_file = request.FILES.get('zip_file')
            if zip_file:
                summaries.append(('ZIP', handle_zip_upload(zip_file, uploaded_by=request.user, hint_class=hint_class)))
            for label, summary in summaries:
                messages.info(
                    request,
                    f'{label}: created {summary.created}, invalid {summary.invalid}, skipped {summary.skipped}.',
                )
                for error in summary.errors[:8]:
                    messages.warning(request, error)
            return image_list_redirect(hint_class.id if hint_class else '')
    else:
        form = ImageUploadForm(initial={'object_class': request.GET.get('class', '')})
    return render(request, 'datasets/image_upload.html', {'form': form})


def delete_uploaded_image(image):
    image_file = image.file
    image.delete()
    if image_file:
        image_file.delete(save=False)


@login_required
@require_POST
def image_delete(request, pk):
    image = get_object_or_404(UploadedImage, pk=pk)
    original_filename = image.original_filename
    delete_uploaded_image(image)
    messages.success(request, f'Image deleted: {original_filename}')
    return image_list_redirect(request.POST.get('class'))


@login_required
@require_POST
def image_bulk_delete(request):
    image_ids = request.POST.getlist('image_ids')
    images = list(UploadedImage.objects.filter(id__in=image_ids))
    if not images:
        messages.warning(request, 'No images selected.')
        return image_list_redirect(request.POST.get('class'))

    count = len(images)
    for image in images:
        delete_uploaded_image(image)
    messages.success(request, f'{count} image(s) deleted.')
    return image_list_redirect(request.POST.get('class'))


@login_required
def dataset_build(request):
    warnings = dataset_warnings()
    if request.method == 'POST':
        form = DatasetBuildForm(request.POST)
        if form.is_valid():
            try:
                dataset_version = build_dataset_version(form, user=request.user, use_augmentation=False)
                messages.success(request, f'DatasetVersion built: {dataset_version.name}')
                for warning in dataset_version.class_summary_json.get('warnings', [])[:8]:
                    messages.warning(request, warning)
                return redirect('datasets:dataset_version_list')
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = DatasetBuildForm(initial={'train_ratio': 80, 'val_ratio': 10, 'test_ratio': 10, 'random_seed': 42})
    return render(request, 'datasets/dataset_build.html', {'form': form, 'warnings': warnings})


def augmented_preview(target_images_per_class=500):
    counts = source_image_counts_by_class(include_only_labeled_images=True)
    classes = ObjectClass.objects.filter(is_active=True).order_by('sort_order', 'id', 'name')
    rows = []
    for object_class in classes:
        original_count = counts.get(object_class.id, 0)
        rows.append({
            'name': object_class.name,
            'display_name': object_class.display_name,
            'original_count': original_count,
            'target_count': target_images_per_class,
        })
    return {
        'rows': rows,
        'expected_total': len(rows) * target_images_per_class,
        'has_low_source_count': any(row['original_count'] < 10 for row in rows),
    }


@login_required
def augmented_dataset_build(request):
    target = 500
    if request.method == 'POST':
        form = AugmentedDatasetBuildForm(request.POST)
        if form.is_valid():
            target = form.cleaned_data.get('target_images_per_class') or 500
            try:
                dataset_version = prepare_augmented_dataset_version(form, user=request.user)
                start_augmented_dataset_build(dataset_version)
                messages.success(request, f'Augmented DatasetVersion build started: {dataset_version.name}')
                messages.info(request, 'The build is running in the background. This page refreshes while a build is pending.')
                for warning in dataset_version.class_summary_json.get('warnings', [])[:8]:
                    messages.warning(request, warning)
                return redirect('datasets:dataset_version_list')
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = AugmentedDatasetBuildForm(initial={
            'train_ratio': 80,
            'val_ratio': 10,
            'test_ratio': 10,
            'random_seed': 42,
            'target_images_per_class': 500,
            'max_augmentations_per_source_image': 100,
            'color_safe_augmentation': True,
        })
    warnings = dataset_warnings(augmentation_options={'use_augmentation': True, 'target_images_per_class': target})
    context = {
        'form': form,
        'warnings': warnings,
        'preview': augmented_preview(target),
    }
    return render(request, 'datasets/augmented_dataset_build.html', context)


@login_required
def dataset_version_list(request):
    versions = DatasetVersion.objects.select_related('created_by')[:100]
    return render(request, 'datasets/dataset_version_list.html', {
        'versions': versions,
        'has_active_builds': any(version.status == DatasetVersion.Status.PENDING for version in versions),
    })
