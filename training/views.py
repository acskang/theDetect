from pathlib import Path
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import TrainingJobForm
from .models import TrainingJob
from .runner import start_training_job, yolo_available

PENDING_JOB_ACTIVE_WINDOW = timedelta(minutes=10)


def is_active_training_job(job):
    if job.status == TrainingJob.Status.RUNNING:
        return True
    if job.status != TrainingJob.Status.PENDING:
        return False
    return job.created_at >= timezone.now() - PENDING_JOB_ACTIVE_WINDOW


@login_required
def job_list(request):
    if request.method == 'POST':
        form = TrainingJobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            start_training_job(job)
            messages.success(request, f'Training job started: {job.name}')
            return redirect('training:job_detail', job_id=job.id)
    else:
        form = TrainingJobForm(initial={
            'base_model': 'yolo11n.pt',
            'imgsz': 640,
            'epochs': 50,
            'batch': 16,
            'device': '0',
            'patience': 20,
            'workers': 'auto',
        })
    jobs = list(TrainingJob.objects.select_related('dataset_version')[:100])
    for job in jobs:
        job.latest_log_line = ''
        if job.log_file and Path(job.log_file).exists():
            lines = Path(job.log_file).read_text(encoding='utf-8', errors='replace').splitlines()
            job.latest_log_line = lines[-1] if lines else ''
    return render(request, 'training/job_list.html', {
        'form': form,
        'jobs': jobs,
        'yolo_available': yolo_available(),
        'has_active_jobs': any(is_active_training_job(job) for job in jobs),
    })


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(TrainingJob.objects.select_related('dataset_version'), pk=job_id)
    latest_log = ''
    if job.log_file and Path(job.log_file).exists():
        latest_log = Path(job.log_file).read_text(encoding='utf-8', errors='replace')[-12000:]
    return render(request, 'training/job_detail.html', {
        'job': job,
        'latest_log': latest_log,
        'is_active_job': is_active_training_job(job),
    })
