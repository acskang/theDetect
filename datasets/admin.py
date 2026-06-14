from django.contrib import admin

from .models import DatasetVersion, ObjectClass, UploadedImage


@admin.register(ObjectClass)
class ObjectClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'color', 'is_active', 'sort_order', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'display_name')
    ordering = ('sort_order', 'name')


@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'status', 'upload_source', 'hint_class', 'width', 'height', 'file_size', 'created_at')
    list_filter = ('status', 'upload_source', 'hint_class')
    search_fields = ('original_filename',)
    readonly_fields = ('width', 'height', 'file_size', 'created_at', 'updated_at')


@admin.register(DatasetVersion)
class DatasetVersionAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'train_ratio', 'val_ratio', 'test_ratio', 'random_seed', 'created_at')
    list_filter = ('status',)
    search_fields = ('name',)
    readonly_fields = ('class_summary_json', 'build_config_json', 'output_path', 'created_at')
