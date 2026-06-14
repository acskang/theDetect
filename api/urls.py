from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'api'

urlpatterns = [
    path('health/', views.health, name='health'),
    path('auth/signup/', views.signup, name='signup'),
    path('auth/login/', views.PhoneOrUsernameTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/session/refresh/', views.session_refresh, name='session_refresh'),
    path('auth/protected-test/', views.protected_test, name='protected_test'),
    path('models/android/latest/', views.latest_android_model, name='latest_android_model'),
    path('models/android/latest/<str:filename>', views.latest_android_model_file, name='latest_android_model_file'),
    path('detect/server/', views.detect_server, name='detect_server'),
    path('detection-logs/', views.detection_logs, name='detection_logs'),
]
