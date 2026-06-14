from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import TrainedModel


@login_required
def registry(request):
    models = TrainedModel.objects.select_related('training_job')[:100]
    return render(request, 'models_registry/registry.html', {'models': models})


@login_required
@require_POST
def activate(request, model_id):
    trained_model = get_object_or_404(TrainedModel, pk=model_id)
    with transaction.atomic():
        TrainedModel.objects.exclude(pk=trained_model.pk).update(is_active_server_model=False)
        trained_model.is_active_server_model = True
        trained_model.save(update_fields=['is_active_server_model'])
    messages.success(request, f'Active server model set: {trained_model.name}')
    return redirect('models_registry:registry')
