from django.contrib import admin

from .models import TrainingJob


@admin.register(TrainingJob)
class TrainingJobAdmin(admin.ModelAdmin):
    list_display = ('name', 'dataset_version', 'base_model', 'epochs', 'batch', 'device', 'status', 'created_at')
    list_filter = ('status', 'base_model', 'device')
    search_fields = ('name', 'dataset_version__name')
    readonly_fields = ('started_at', 'finished_at', 'log_file', 'artifacts_path', 'metrics_json', 'error_message', 'created_at')
