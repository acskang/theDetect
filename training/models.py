from django.conf import settings
from django.db import models


class TrainingJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELED = 'canceled', 'Canceled'

    name = models.CharField(max_length=120, unique=True)
    dataset_version = models.ForeignKey('datasets.DatasetVersion', on_delete=models.PROTECT, related_name='training_jobs')
    base_model = models.CharField(max_length=120, default='yolo11n.pt')
    imgsz = models.PositiveIntegerField(default=640)
    epochs = models.PositiveIntegerField(default=50)
    batch = models.IntegerField(default=16)
    device = models.CharField(max_length=80, default='0')
    patience = models.PositiveIntegerField(default=20)
    workers = models.CharField(max_length=40, default='auto')
    memo = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    log_file = models.CharField(max_length=500, blank=True)
    artifacts_path = models.CharField(max_length=500, blank=True)
    metrics_json = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='training_jobs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
