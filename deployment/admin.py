from django.contrib import admin

from .models import AndroidModelPackage


@admin.register(AndroidModelPackage)
class AndroidModelPackageAdmin(admin.ModelAdmin):
    list_display = ('model_version', 'trained_model', 'status', 'input_size', 'is_deployed', 'created_at', 'deployed_at')
    list_filter = ('status', 'is_deployed')
    search_fields = ('name', 'model_version', 'trained_model__name')
    readonly_fields = ('export_log', 'error_message', 'created_at', 'deployed_at')
