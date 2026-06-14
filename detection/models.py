from django.conf import settings
from django.db import models


class DetectionLog(models.Model):
    class Mode(models.TextChoices):
        SERVER = 'server', 'Server'
        ON_DEVICE = 'on_device', 'On-device'

    class ReviewStatus(models.TextChoices):
        UNKNOWN = 'unknown', 'Unknown'
        CORRECT = 'correct', 'Correct'
        WRONG = 'wrong', 'Wrong'
        IGNORED = 'ignored', 'Ignored'

    mode = models.CharField(max_length=20, choices=Mode.choices)
    model_version = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to='detection_logs/images/', blank=True)
    thumbnail = models.ImageField(upload_to='detection_logs/thumbnails/', blank=True)
    detections_json = models.JSONField(default=list, blank=True)
    top_class = models.CharField(max_length=120, blank=True)
    top_confidence = models.FloatField(null=True, blank=True)
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)
    device_info = models.TextField(blank=True)
    app_version = models.CharField(max_length=80, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='detection_logs')
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.UNKNOWN)
    actual_class = models.ForeignKey('datasets.ObjectClass', null=True, blank=True, on_delete=models.SET_NULL, related_name='actual_detection_logs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.mode} {self.model_version or "unversioned"}'
