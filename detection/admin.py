from django.contrib import admin

from .models import DetectionLog


@admin.register(DetectionLog)
class DetectionLogAdmin(admin.ModelAdmin):
    list_display = ('mode', 'model_version', 'top_class', 'top_confidence', 'review_status', 'created_at')
    list_filter = ('mode', 'review_status')
    search_fields = ('model_version', 'top_class', 'device_info')
    readonly_fields = ('created_at',)
