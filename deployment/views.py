from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from pathlib import Path

from .exporter import start_export_package
from .forms import AndroidModelExportForm
from .models import AndroidModelPackage


@login_required
def android_export(request):
    if request.method == 'POST':
        form = AndroidModelExportForm(request.POST)
        if form.is_valid():
            package = form.save(commit=False)
            package.name = package.model_version
            package.created_by = request.user
            package.status = AndroidModelPackage.Status.PENDING
            package.export_log = form.cleaned_data.get('export_memo', '')
            package.save()
            start_export_package(package)
            messages.success(request, f'Android model export started: {package.model_version}')
            return redirect('deployment:package_detail', package_id=package.id)
    else:
        form = AndroidModelExportForm(initial={
            'input_size': 640,
            'confidence_threshold': 0.5,
            'iou_threshold': 0.45,
        })
    packages = AndroidModelPackage.objects.select_related('trained_model')[:20]
    return render(request, 'deployment/android_export.html', {
        'form': form,
        'packages': packages,
        'has_active_packages': any(package.status in {AndroidModelPackage.Status.PENDING, AndroidModelPackage.Status.RUNNING} for package in packages),
    })


@login_required
def package_list(request):
    packages = AndroidModelPackage.objects.select_related('trained_model')[:100]
    return render(request, 'deployment/package_list.html', {
        'packages': packages,
        'has_active_packages': any(package.status in {AndroidModelPackage.Status.PENDING, AndroidModelPackage.Status.RUNNING} for package in packages),
    })


@login_required
def package_detail(request, package_id):
    package = get_object_or_404(AndroidModelPackage.objects.select_related('trained_model__training_job__dataset_version'), pk=package_id)
    export_log_text = package.export_log
    if package.export_log and Path(package.export_log).exists():
        export_log_text = Path(package.export_log).read_text(encoding='utf-8', errors='replace')[-12000:]
    return render(request, 'deployment/package_detail.html', {
        'package': package,
        'export_log_text': export_log_text,
        'is_active_package': package.status in {AndroidModelPackage.Status.PENDING, AndroidModelPackage.Status.RUNNING},
    })


@login_required
@require_POST
def deploy_package(request, package_id):
    package = get_object_or_404(AndroidModelPackage, pk=package_id)
    if package.status != AndroidModelPackage.Status.COMPLETED:
        messages.error(request, 'Only completed Android model packages can be deployed.')
    elif not (package.tflite_file and package.labels_file and package.metadata_file):
        messages.error(request, 'Package files are incomplete.')
    else:
        package.mark_deployed()
        messages.success(request, f'Deployed Android model package: {package.model_version}')
    return redirect('deployment:package_detail', package_id=package.id)
