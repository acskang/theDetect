from django.contrib import admin

from .models import LabelBox


@admin.register(LabelBox)
class LabelBoxAdmin(admin.ModelAdmin):
    list_display = ('image', 'object_class', 'x_min', 'y_min', 'x_max', 'y_max', 'review_status', 'updated_at')
    list_filter = ('review_status', 'object_class')
    search_fields = ('image__original_filename', 'object_class__name')
    readonly_fields = ('created_at', 'updated_at')
