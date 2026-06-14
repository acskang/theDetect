from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('healthz/', views.healthz, name='healthz'),
    path('readyz/', views.readyz, name='readyz'),
    path('api/llama/chat/', views.llama_chat, name='llama_chat'),
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manual/', views.manual_home, name='manual'),
    path('manual/apk/latest/download/', views.manual_apk_download, name='manual_apk_download'),
    path('manual/view/<path:doc_path>/', views.manual_view, name='manual_view'),
    path('manual/raw/<path:doc_path>/', views.manual_raw, name='manual_raw'),
    path('server-detection/', views.server_detection, name='server_detection'),
    path('api-test/', views.api_test, name='api_test'),
    path('project-settings/', views.project_settings, name='project_settings'),
    path('detection-logs/', views.detection_logs, name='detection_logs'),
    path('review-queue/', views.placeholder, {'page_name': 'Review Queue'}, name='review_queue'),
]
