from django.contrib import admin

from .models import TrainedModel


@admin.register(TrainedModel)
class TrainedModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'training_job', 'model_format', 'is_active_server_model', 'created_at')
    list_filter = ('model_format', 'is_active_server_model')
    search_fields = ('name', 'model_path')
    readonly_fields = ('created_at',)
