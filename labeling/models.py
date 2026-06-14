from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class LabelBox(models.Model):
    class ReviewStatus(models.TextChoices):
        UNKNOWN = 'unknown', 'Unknown'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        NEEDS_REVIEW = 'needs_review', 'Needs review'

    image = models.ForeignKey('datasets.UploadedImage', on_delete=models.CASCADE, related_name='label_boxes')
    object_class = models.ForeignKey('datasets.ObjectClass', on_delete=models.PROTECT, related_name='label_boxes')
    x_min = models.PositiveIntegerField()
    y_min = models.PositiveIntegerField()
    x_max = models.PositiveIntegerField()
    y_max = models.PositiveIntegerField()
    image_width = models.PositiveIntegerField()
    image_height = models.PositiveIntegerField()
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.UNKNOWN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='label_boxes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['image_id', 'id']

    def clean(self):
        errors = {}
        if self.x_min >= self.x_max:
            errors['x_max'] = 'x_max must be greater than x_min.'
        if self.y_min >= self.y_max:
            errors['y_max'] = 'y_max must be greater than y_min.'
        if self.x_max > self.image_width:
            errors['x_max'] = 'x_max cannot exceed image_width.'
        if self.y_max > self.image_height:
            errors['y_max'] = 'y_max cannot exceed image_height.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.image_id}: {self.object_class} ({self.x_min}, {self.y_min}, {self.x_max}, {self.y_max})'
