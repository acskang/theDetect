import json
import tempfile
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from datasets.models import DatasetVersion
from models_registry.models import TrainedModel
from training.models import TrainingJob

from .exporter import create_fake_completed_package_files, metadata_for_package, run_export_package, write_labels_and_metadata, yolo_executable
from .models import AndroidModelPackage


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), PROJECT_DATA_DIR=tempfile.mkdtemp())
class AndroidModelPackageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='deploy_user', password='pass')
        self.client.force_login(self.user)
        self.dataset = DatasetVersion.objects.create(
            name='deploy_dataset',
            train_ratio=80,
            val_ratio=10,
            test_ratio=10,
            random_seed=42,
            class_summary_json={'class_names': ['class_01', 'class_02', 'other']},
            output_path='/tmp/deploy_dataset',
            status=DatasetVersion.Status.BUILT,
            created_by=self.user,
        )
        self.job = TrainingJob.objects.create(
            name='deploy_job',
            dataset_version=self.dataset,
            status=TrainingJob.Status.COMPLETED,
            created_by=self.user,
        )
        model_path = Path(tempfile.mkdtemp()) / 'best.pt'
        model_path.write_bytes(b'fake pt')
        self.trained_model = TrainedModel.objects.create(
            name='deploy_model',
            training_job=self.job,
            model_path=str(model_path),
            class_names_json=['class_01', 'class_02', 'other'],
        )

    def create_package(self, version='mdetect_test_001'):
        return AndroidModelPackage.objects.create(
            name=version,
            trained_model=self.trained_model,
            model_version=version,
            input_size=640,
            confidence_threshold=0.5,
            iou_threshold=0.45,
            created_by=self.user,
        )

    def test_android_model_package_model_creation(self):
        package = self.create_package()

        self.assertEqual(package.status, AndroidModelPackage.Status.PENDING)
        self.assertEqual(package.trained_model, self.trained_model)

    def test_labels_and_metadata_generation(self):
        package = self.create_package()

        labels_path, metadata_path = write_labels_and_metadata(package)
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))

        self.assertEqual(labels_path.read_text(encoding='utf-8'), 'class_01\nclass_02\nother\n')
        self.assertEqual(metadata['model_version'], package.model_version)
        self.assertEqual(metadata['classes'], ['class_01', 'class_02', 'other'])

    def test_metadata_helper_contains_expected_ids(self):
        package = self.create_package()

        metadata = metadata_for_package(package, ['class_01'])

        self.assertEqual(metadata['trained_model_id'], self.trained_model.id)
        self.assertEqual(metadata['training_job_id'], self.job.id)
        self.assertEqual(metadata['dataset_version_id'], self.dataset.id)

    def test_deployed_model_singleton(self):
        first = self.create_package('mdetect_test_001')
        second = self.create_package('mdetect_test_002')
        first.mark_deployed()
        second.mark_deployed()

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_deployed)
        self.assertTrue(second.is_deployed)

    def test_export_screen_returns_200(self):
        response = self.client.get('/models/android/export/')

        self.assertEqual(response.status_code, 200)

    def test_package_list_screen_returns_200(self):
        response = self.client.get('/models/android/packages/')

        self.assertEqual(response.status_code, 200)

    def test_package_detail_screen_returns_200(self):
        package = self.create_package()

        response = self.client.get(f'/models/android/packages/{package.id}/')

        self.assertEqual(response.status_code, 200)

    def test_yolo_executable_prefers_configured_export_environment(self):
        bin_dir = Path(tempfile.mkdtemp()) / 'bin'
        bin_dir.mkdir()
        yolo_path = bin_dir / 'yolo'
        yolo_path.write_text('#!/bin/sh\n', encoding='utf-8')

        with override_settings(MDETECT_EXPORT_YOLO_BIN=str(yolo_path)):
            self.assertEqual(yolo_executable(), str(yolo_path))

    def test_failed_export_deletes_package_record(self):
        package = self.create_package('failed_export_version')

        with (
            patch('deployment.exporter.yolo_executable', return_value='/tmp/fake-yolo'),
            patch('deployment.exporter.subprocess.run', return_value=SimpleNamespace(returncode=1)),
        ):
            run_export_package(package.id)

        self.assertFalse(AndroidModelPackage.objects.filter(model_version='failed_export_version').exists())
