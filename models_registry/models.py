from django.db import models


class TrainedModel(models.Model):
    name = models.CharField(max_length=120)
    training_job = models.OneToOneField('training.TrainingJob', on_delete=models.CASCADE, related_name='trained_model')
    model_path = models.CharField(max_length=500)
    model_format = models.CharField(max_length=40, default='pt')
    class_names_json = models.JSONField(default=list, blank=True)
    metrics_json = models.JSONField(default=dict, blank=True)
    is_active_server_model = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
