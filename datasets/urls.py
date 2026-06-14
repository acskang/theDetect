from django.urls import path

from . import views

app_name = 'datasets'

urlpatterns = [
    path('classes/', views.object_class_list, name='object_class_list'),
    path('classes/create/', views.object_class_create, name='object_class_create'),
    path('classes/<int:pk>/edit/', views.object_class_edit, name='object_class_edit'),
    path('datasets/images/', views.image_list, name='image_list'),
    path('datasets/images/upload/', views.image_upload, name='image_upload'),
    path('datasets/images/bulk-delete/', views.image_bulk_delete, name='image_bulk_delete'),
    path('datasets/images/<int:pk>/delete/', views.image_delete, name='image_delete'),
    path('datasets/build/', views.dataset_build, name='dataset_build'),
    path('datasets/build/augmented/', views.augmented_dataset_build, name='augmented_dataset_build'),
    path('datasets/versions/', views.dataset_version_list, name='dataset_version_list'),
]
