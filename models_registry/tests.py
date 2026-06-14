from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from io import StringIO

from datasets.models import DatasetVersion
from training.models import TrainingJob

from .models import TrainedModel


class ModelRegistryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='registry', password='pass')
        self.client.force_login(self.user)
        self.dataset = DatasetVersion.objects.create(
            name='registry_dataset',
            train_ratio=80,
            val_ratio=10,
            test_ratio=10,
            random_seed=42,
            output_path='/tmp/registry_dataset',
            status=DatasetVersion.Status.BUILT,
            created_by=self.user,
        )
        self.job = TrainingJob.objects.create(name='registry_job', dataset_version=self.dataset, created_by=self.user)

    def test_model_registry_screen_returns_200(self):
        TrainedModel.objects.create(name='model_one', training_job=self.job, model_path='/tmp/best.pt')

        response = self.client.get('/models/registry/')

        self.assertEqual(response.status_code, 200)

    def test_activate_model_deactivates_other_models(self):
        other_job = TrainingJob.objects.create(name='registry_job_two', dataset_version=self.dataset, created_by=self.user)
        first = TrainedModel.objects.create(
            name='model_one',
            training_job=self.job,
            model_path='/tmp/best.pt',
            is_active_server_model=True,
        )
        second = TrainedModel.objects.create(name='model_two', training_job=other_job, model_path='/tmp/second.pt')

        response = self.client.post(f'/models/registry/{second.id}/activate/')

        self.assertEqual(response.status_code, 302)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_active_server_model)
        self.assertTrue(second.is_active_server_model)

    def test_set_active_model_command_deactivates_other_models(self):
        other_job = TrainingJob.objects.create(name='registry_job_three', dataset_version=self.dataset, created_by=self.user)
        first = TrainedModel.objects.create(
            name='model_one',
            training_job=self.job,
            model_path='/tmp/best.pt',
            is_active_server_model=True,
        )
        second = TrainedModel.objects.create(name='model_two', training_job=other_job, model_path='/tmp/second.pt')
        out = StringIO()

        call_command('set_active_model', '--id', str(second.id), '--allow-missing-file', stdout=out)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_active_server_model)
        self.assertTrue(second.is_active_server_model)
        self.assertIn('Active server model set', out.getvalue())
