import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from datasets.models import DatasetVersion

from .models import TrainingJob
from .runner import yolo_executable, yolo_subprocess_env


class TrainingJobTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='trainer', password='pass')
        self.client.force_login(self.user)
        self.dataset = DatasetVersion.objects.create(
            name='built_dataset',
            train_ratio=80,
            val_ratio=10,
            test_ratio=10,
            random_seed=42,
            class_summary_json={'data_yaml': '/tmp/data.yaml', 'class_names': ['class_01']},
            output_path='/tmp/built_dataset',
            status=DatasetVersion.Status.BUILT,
            created_by=self.user,
        )

    def test_training_job_model_creation(self):
        job = TrainingJob.objects.create(
            name='job_one',
            dataset_version=self.dataset,
            base_model='yolo11n.pt',
            created_by=self.user,
        )

        self.assertEqual(job.status, TrainingJob.Status.PENDING)
        self.assertEqual(job.imgsz, 640)
        self.assertEqual(job.device, '0')

    def test_training_jobs_screen_returns_200(self):
        response = self.client.get('/training/jobs/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="0"')

    def test_training_job_detail_returns_200(self):
        job = TrainingJob.objects.create(name='job_detail', dataset_version=self.dataset, created_by=self.user)

        response = self.client.get(f'/training/jobs/{job.id}/')

        self.assertEqual(response.status_code, 200)

    def test_yolo_executable_falls_back_to_current_python_environment(self):
        with TemporaryDirectory() as temp_dir:
            bin_dir = Path(temp_dir) / 'bin'
            bin_dir.mkdir()
            python_path = bin_dir / 'python'
            yolo_path = bin_dir / 'yolo'
            python_path.write_text('', encoding='utf-8')
            yolo_path.write_text('', encoding='utf-8')
            yolo_path.chmod(yolo_path.stat().st_mode | os.X_OK)

            with patch('training.runner.shutil.which', return_value=None), patch('training.runner.sys.executable', str(python_path)):
                self.assertEqual(yolo_executable(), str(yolo_path))

    def test_yolo_subprocess_env_adds_cuda_library_path(self):
        with TemporaryDirectory() as temp_dir:
            env_root = Path(temp_dir)
            python_path = env_root / 'bin' / 'python'
            cuda_lib = env_root / 'lib' / 'python3.13' / 'site-packages' / 'nvidia' / 'cu13' / 'lib'
            python_path.parent.mkdir()
            cuda_lib.mkdir(parents=True)
            python_path.write_text('', encoding='utf-8')

            with patch('training.runner.sys.executable', str(python_path)), patch.dict(os.environ, {'LD_LIBRARY_PATH': '/existing'}, clear=True):
                env = yolo_subprocess_env()

            self.assertEqual(env['LD_LIBRARY_PATH'], f'{cuda_lib}{os.pathsep}/existing')
