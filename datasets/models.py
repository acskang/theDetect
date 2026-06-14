from django.conf import settings
from django.db import models


class ObjectClass(models.Model):
    name = models.SlugField(max_length=80, unique=True)
    display_name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#2563eb')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.display_name or self.name


def uploaded_image_path(instance, filename):
    return f'uploads/images/{instance.upload_source}/{filename}'


class UploadedImage(models.Model):
    class UploadSource(models.TextChoices):
        MULTI = 'multi', 'Multi'
        ZIP = 'zip', 'ZIP'
        MANUAL = 'manual', 'Manual'

    class Status(models.TextChoices):
        UPLOADED = 'uploaded', 'Uploaded'
        LABELING = 'labeling', 'Labeling'
        LABELED = 'labeled', 'Labeled'
        INVALID = 'invalid', 'Invalid'
        EXCLUDED = 'excluded', 'Excluded'

    file = models.ImageField(upload_to=uploaded_image_path)
    original_filename = models.CharField(max_length=255)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    file_size = models.PositiveBigIntegerField(default=0)
    upload_source = models.CharField(max_length=20, choices=UploadSource.choices, default=UploadSource.MANUAL)
    hint_class = models.ForeignKey(ObjectClass, null=True, blank=True, on_delete=models.SET_NULL, related_name='hint_images')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='uploaded_images')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.original_filename


class DatasetVersion(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        BUILT = 'built', 'Built'
        FAILED = 'failed', 'Failed'

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    train_ratio = models.PositiveIntegerField(default=80)
    val_ratio = models.PositiveIntegerField(default=10)
    test_ratio = models.PositiveIntegerField(default=10)
    random_seed = models.PositiveIntegerField(default=42)
    class_summary_json = models.JSONField(default=dict, blank=True)
    build_config_json = models.JSONField(default=dict, blank=True)
    output_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='dataset_versions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
