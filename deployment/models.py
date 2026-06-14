from django.conf import settings
from django.db import models
from django.utils import timezone


class AndroidModelPackage(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    name = models.CharField(max_length=120)
    trained_model = models.ForeignKey('models_registry.TrainedModel', on_delete=models.PROTECT, related_name='android_packages')
    model_version = models.SlugField(max_length=120, unique=True)
    tflite_file = models.FileField(upload_to='android_exports/%Y/%m/', blank=True)
    labels_file = models.FileField(upload_to='android_exports/%Y/%m/', blank=True)
    metadata_file = models.FileField(upload_to='android_exports/%Y/%m/', blank=True)
    input_size = models.PositiveIntegerField(default=640)
    confidence_threshold = models.FloatField(default=0.5)
    iou_threshold = models.FloatField(default=0.45)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    export_log = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    is_deployed = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='android_model_packages')
    created_at = models.DateTimeField(auto_now_add=True)
    deployed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.model_version

    def mark_deployed(self):
        AndroidModelPackage.objects.exclude(pk=self.pk).update(is_deployed=False, deployed_at=None)
        self.is_deployed = True
        self.deployed_at = timezone.now()
        self.save(update_fields=['is_deployed', 'deployed_at'])
