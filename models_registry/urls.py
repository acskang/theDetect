from django.urls import path

from . import views

app_name = 'models_registry'

urlpatterns = [
    path('registry/', views.registry, name='registry'),
    path('registry/<int:model_id>/activate/', views.activate, name='activate'),
]
