import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import AccountProfile
from datasets.models import DatasetVersion
from detection.models import DetectionLog
from deployment.exporter import create_fake_completed_package_files
from deployment.models import AndroidModelPackage
from models_registry.models import TrainedModel
from training.models import TrainingJob


class ApiAuthTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='api_user', password='secret-pass')
        AccountProfile.objects.create(user=self.user, phone_number='01012345678')

    def test_health_is_public(self):
        response = self.client.get('/api/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['service'], 'MDetect')

    def test_jwt_login_refresh_and_protected_test(self):
        login = self.client.post(
            '/api/auth/login/',
            {'username': 'api_user', 'password': 'secret-pass'},
            content_type='application/json',
        )
        self.assertEqual(login.status_code, 200)
        tokens = login.json()

        refresh = self.client.post(
            '/api/auth/refresh/',
            {'refresh': tokens['refresh']},
            content_type='application/json',
        )
        self.assertEqual(refresh.status_code, 200)

        protected = self.client.get(
            '/api/auth/protected-test/',
            HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}',
        )
        self.assertEqual(protected.status_code, 200)
        self.assertEqual(protected.json()['user']['username'], 'api_user')

    def test_jwt_login_accepts_phone_number_in_username_field(self):
        login = self.client.post(
            '/api/auth/login/',
            {'username': '010-1234-5678', 'password': 'secret-pass'},
            content_type='application/json',
        )

        self.assertEqual(login.status_code, 200)
        self.assertIn('access', login.json())


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), PROJECT_DATA_DIR=tempfile.mkdtemp())
class AndroidModelApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='android_api', password='pass')
        refresh = RefreshToken.for_user(self.user)
        self.auth_header = f'Bearer {refresh.access_token}'
        dataset = DatasetVersion.objects.create(
            name='api_dataset',
            train_ratio=80,
            val_ratio=10,
            test_ratio=10,
            random_seed=42,
            class_summary_json={'class_names': ['class_01', 'class_02', 'other']},
            output_path='/tmp/api_dataset',
            status=DatasetVersion.Status.BUILT,
            created_by=self.user,
        )
        job = TrainingJob.objects.create(
            name='api_job',
            dataset_version=dataset,
            status=TrainingJob.Status.COMPLETED,
            created_by=self.user,
        )
        model_path = Path(tempfile.mkdtemp()) / 'best.pt'
        model_path.write_bytes(b'fake pt')
        trained_model = TrainedModel.objects.create(
            name='api_model',
            training_job=job,
            model_path=str(model_path),
            class_names_json=['class_01', 'class_02', 'other'],
        )
        self.package = AndroidModelPackage.objects.create(
            name='mdetect_api_001',
            trained_model=trained_model,
            model_version='mdetect_api_001',
            input_size=640,
            confidence_threshold=0.5,
            iou_threshold=0.45,
            created_by=self.user,
        )
        create_fake_completed_package_files(self.package)
        self.package.mark_deployed()

    def image_upload(self, name='frame.jpg', size=(20, 10)):
        buffer = BytesIO()
        Image.new('RGB', size, color='black').save(buffer, format='JPEG')
        return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/jpeg')

    def test_latest_model_info_api(self):
        response = self.client.get('/api/models/android/latest/', HTTP_AUTHORIZATION=self.auth_header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['model_version'], 'mdetect_api_001')
        self.assertEqual(response.json()['classes'], ['class_01', 'class_02', 'other'])

    def test_model_tflite_download_api(self):
        response = self.client.get('/api/models/android/latest/model.tflite', HTTP_AUTHORIZATION=self.auth_header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/octet-stream')

    def test_labels_download_api(self):
        response = self.client.get('/api/models/android/latest/labels.txt', HTTP_AUTHORIZATION=self.auth_header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/plain')

    def test_metadata_download_api(self):
        response = self.client.get('/api/models/android/latest/metadata.json', HTTP_AUTHORIZATION=self.auth_header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/json')

    def test_latest_model_requires_auth(self):
        response = self.client.get('/api/models/android/latest/')

        self.assertEqual(response.status_code, 401)

    def test_server_detection_api_returns_stable_json(self):
        response = self.client.post(
            '/api/detect/server/',
            {'image': self.image_upload()},
            HTTP_AUTHORIZATION=self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['mode'], 'server')
        self.assertFalse(payload['model_available'])
        self.assertIn('detections', payload)
        self.assertEqual(payload['image_width'], 20)
        self.assertEqual(payload['image_height'], 10)
        self.assertIsNone(payload['log_id'])

    def test_server_detection_requires_jwt(self):
        response = self.client.post('/api/detect/server/', {'image': self.image_upload()})

        self.assertEqual(response.status_code, 401)

    def test_server_detection_requires_image(self):
        response = self.client.post('/api/detect/server/', {}, HTTP_AUTHORIZATION=self.auth_header)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'image is required.')

    def test_server_detection_rejects_invalid_image(self):
        upload = SimpleUploadedFile('frame.jpg', b'not an image', content_type='image/jpeg')

        response = self.client.post(
            '/api/detect/server/',
            {'image': upload},
            HTTP_AUTHORIZATION=self.auth_header,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('valid image', response.json()['message'])

    def test_server_detection_returns_mocked_yolo_detection_and_saves_log(self):
        self.package.trained_model.is_active_server_model = True
        self.package.trained_model.save(update_fields=['is_active_server_model'])

        with patch('detection.services.yolo_inference.get_cached_yolo_model', return_value=FakeYoloModel()):
            response = self.client.post(
                '/api/detect/server/',
                {
                    'image': self.image_upload(size=(40, 30)),
                    'device_info': 'test-device',
                    'app_version': '1.0.0',
                },
                HTTP_AUTHORIZATION=self.auth_header,
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['model_available'])
        self.assertEqual(payload['message'], 'ok')
        self.assertEqual(payload['model_version'], 'api_model')
        self.assertEqual(payload['detections'][0]['class_id'], 0)
        self.assertEqual(payload['detections'][0]['class_name'], 'class_01')
        self.assertEqual(payload['detections'][0]['box'], {'x_min': 1, 'y_min': 2, 'x_max': 11, 'y_max': 12})

        log = DetectionLog.objects.get(pk=payload['log_id'])
        self.assertEqual(log.top_class, 'class_01')
        self.assertAlmostEqual(log.top_confidence, 0.876543)
        self.assertEqual(log.device_info, 'test-device')
        self.assertEqual(log.app_version, '1.0.0')
        self.assertEqual(log.detections_json, payload['detections'])

    def test_server_detection_active_model_missing_file_returns_stable_json(self):
        self.package.trained_model.model_path = '/tmp/mdetect_missing_model.pt'
        self.package.trained_model.is_active_server_model = True
        self.package.trained_model.save(update_fields=['model_path', 'is_active_server_model'])

        response = self.client.post(
            '/api/detect/server/',
            {'image': self.image_upload()},
            HTTP_AUTHORIZATION=self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['model_available'])
        self.assertIn('does not exist', response.json()['message'])

    def test_detection_logs_api_returns_results_wrapper(self):
        DetectionLog.objects.create(mode=DetectionLog.Mode.SERVER, model_version='test_model', user=self.user)

        response = self.client.get('/api/detection-logs/', HTTP_AUTHORIZATION=self.auth_header)

        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json())
        self.assertEqual(response.json()['results'][0]['model_version'], 'test_model')


class FakeBoxes:
    xyxy = [[1.2, 2.4, 10.6, 11.8]]
    conf = [0.876543]
    cls = [0]


class FakeResult:
    boxes = FakeBoxes()


class FakeYoloModel:
    names = {0: 'model_name_should_not_win'}

    def __call__(self, image, conf, iou, imgsz, verbose):
        return [FakeResult()]
