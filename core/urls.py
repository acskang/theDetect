from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('healthz/', views.healthz, name='healthz'),
    path('readyz/', views.readyz, name='readyz'),
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manual/', views.manual_home, name='manual'),
    path('manual/view/<path:doc_path>/', views.manual_view, name='manual_view'),
    path('manual/raw/<path:doc_path>/', views.manual_raw, name='manual_raw'),
    path('server-detection/', views.server_detection, name='server_detection'),
    path('api-test/', views.api_test, name='api_test'),
    path('project-settings/', views.placeholder, {'page_name': 'Project Settings'}, name='project_settings'),
    path('detection-logs/', views.placeholder, {'page_name': 'Detection Logs'}, name='detection_logs'),
    path('review-queue/', views.placeholder, {'page_name': 'Review Queue'}, name='review_queue'),
]
