from django.urls import path

from . import views

app_name = 'labeling'

urlpatterns = [
    path('', views.workspace, name='workspace'),
    path('auto/rough-boxes/', views.auto_rough_boxes, name='auto_rough_boxes'),
    path('auto/duplicate-previous/', views.duplicate_previous, name='duplicate_previous'),
    path('auto/active-model/', views.auto_label_active_model, name='auto_label_active_model'),
    path('images/<int:image_id>/', views.editor, name='editor'),
    path('images/<int:image_id>/boxes/save/', views.save_boxes, name='save_boxes'),
    path('images/<int:image_id>/complete/', views.complete_image, name='complete_image'),
    path('images/<int:image_id>/next/', views.next_image, name='next_image'),
]
