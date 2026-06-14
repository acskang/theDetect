from django.urls import path

from . import views

app_name = 'deployment'

urlpatterns = [
    path('android/export/', views.android_export, name='android_export'),
    path('android/packages/', views.package_list, name='package_list'),
    path('android/packages/<int:package_id>/', views.package_detail, name='package_detail'),
    path('android/packages/<int:package_id>/deploy/', views.deploy_package, name='deploy_package'),
]
