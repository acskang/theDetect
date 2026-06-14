import re
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def normalize_phone_number(value):
    return re.sub(r'[\s\-().]', '', value or '')


class AccountProfile(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SUSPENDED = 'suspended', 'Suspended'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mdetect_profile')
    phone_number = models.CharField(max_length=32, unique=True)
    approval_status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.APPROVED)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_mdetect_profiles',
    )
    device_token = models.CharField(max_length=128, blank=True)
    device_token_created_at = models.DateTimeField(null=True, blank=True)
    last_login_device_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    def save(self, *args, **kwargs):
        self.phone_number = normalize_phone_number(self.phone_number)
        if self.approval_status == self.ApprovalStatus.APPROVED and self.approved_at is None:
            self.approved_at = timezone.now()
            update_fields = kwargs.get('update_fields')
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'approved_at'}
        super().save(*args, **kwargs)

    def ensure_device_token(self):
        if not self.device_token:
            self.device_token = secrets.token_urlsafe(48)
            self.device_token_created_at = timezone.now()
        self.last_login_device_at = timezone.now()
        self.save(update_fields=['device_token', 'device_token_created_at', 'last_login_device_at', 'updated_at'])
        return self.device_token

    def __str__(self):
        return f'{self.user.get_username()} / {self.phone_number}'
