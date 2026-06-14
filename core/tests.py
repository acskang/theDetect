from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from datasets.models import DatasetVersion
from detection.models import DetectionLog
from detection.services.yolo_inference import InferenceResult
from models_registry.models import TrainedModel
from training.models import TrainingJob


class LandingAndDashboardTests(TestCase):
    def test_landing_page_is_public(self):
        response = self.client.get(reverse('core:landing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'theDetect')
        self.assertContains(response, '콘솔로 로그인')
        self.assertNotContains(response, 'mdetect_landing_image.png')
        self.assertContains(response, 'Animated cosmetic and shampoo conveyor belt')
        self.assertContains(response, 'startConveyor')
        self.assertContains(response, 'trash-bin')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('core:dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_dashboard_responds_after_login(self):
        user = get_user_model().objects.create_user(username='dashboard_user', password='pass')
        self.client.force_login(user)

        response = self.client.get(reverse('core:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Object Classes')
        self.assertContains(response, 'Server Detection')
        self.assertContains(response, reverse('core:server_detection'))
        self.assertContains(response, 'showSidebar()')
        self.assertContains(response, 'hideSidebar()')
        self.assertContains(response, 'data-nav-open-button')
        self.assertContains(response, 'data-navigation-sidebar')
        self.assertContains(response, 'data-nav-backdrop')
        self.assertContains(response, "'sidebar-collapsed': sidebarCollapsed")
        self.assertContains(response, 'href="/"')
        self.assertContains(response, 'dashboard_user')
        self.assertContains(response, 'action="/accounts/logout/"')
        self.assertContains(response, '>logout</button>')
        self.assertNotContains(response, 'Service URL')


class ManualTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='manual_user', password='pass')

    def test_manual_requires_login(self):
        response = self.client.get(reverse('core:manual'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_manual_menu_is_visible_on_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manual')
        self.assertContains(response, reverse('core:manual'))

    def test_manual_home_redirects_to_first_document(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:manual'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/manual/view/', response['Location'])

    def test_manual_view_renders_document(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:manual_view', kwargs={'doc_path': 'README.md'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Operations Manual')
        self.assertContains(response, 'README')

    def test_manual_raw_view_returns_text(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:manual_raw', kwargs={'doc_path': 'README.md'}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')

    def test_manual_search_renders_results(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:manual_view', kwargs={'doc_path': 'README.md'}), {'q': 'Django'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '검색 결과')


class ServerDetectionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='server_detection_user', password='pass')

    def test_server_detection_requires_login(self):
        response = self.client.get(reverse('core:server_detection'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_server_detection_screen_returns_200(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:server_detection'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test active model')
        self.assertContains(response, 'Run detection')

    def test_server_detection_upload_saves_detection_log(self):
        self.client.force_login(self.user)
        dataset = DatasetVersion.objects.create(
            name='server_detection_dataset',
            train_ratio=80,
            val_ratio=10,
            test_ratio=10,
            random_seed=42,
            class_summary_json={'class_names': ['soap_case_mint']},
            output_path='/tmp/server_detection_dataset',
            status=DatasetVersion.Status.BUILT,
            created_by=self.user,
        )
        job = TrainingJob.objects.create(name='server_detection_job', dataset_version=dataset, created_by=self.user)
        TrainedModel.objects.create(
            name='server_detection_model',
            training_job=job,
            model_path='/tmp/best.pt',
            class_names_json=['soap_case_mint'],
            is_active_server_model=True,
        )
        upload = SimpleUploadedFile('input.png', self.png_bytes(), content_type='image/png')
        inference = InferenceResult(
            detections=[
                {
                    'class_id': 0,
                    'class_name': 'soap_case_mint',
                    'confidence': 0.987654,
                    'box': {'x_min': 1, 'y_min': 2, 'x_max': 20, 'y_max': 30},
                }
            ],
            image_width=32,
            image_height=32,
            model_version='server_detection_model',
        )

        with patch('core.views.run_yolo_inference', return_value=inference):
            response = self.client.post(reverse('core:server_detection'), {'image': upload})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'soap_case_mint')
        self.assertContains(response, '0.987654')
        self.assertEqual(DetectionLog.objects.count(), 1)
        self.assertEqual(DetectionLog.objects.get().top_class, 'soap_case_mint')

    def png_bytes(self):
        buffer = BytesIO()
        Image.new('RGB', (32, 32), color='white').save(buffer, format='PNG')
        return buffer.getvalue()
