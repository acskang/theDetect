from io import BytesIO
from datetime import timezone as datetime_timezone
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from datasets.models import DatasetVersion
from detection.models import DetectionLog
from detection.services.yolo_inference import InferenceResult
from models_registry.models import TrainedModel
from training.models import TrainingJob
from . import manual_services
from .llama_chat import build_manual_context, build_system_prompt, normalize_history, normalize_page_context, page_hints_for_path


class LandingAndDashboardTests(TestCase):
    def test_landing_page_is_public(self):
        response = self.client.get(reverse('core:landing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'theDetect')
        self.assertContains(response, 'login')
        self.assertNotContains(response, '<h2 class="text-2xl font-black">로그인</h2>', html=True)
        self.assertNotContains(response, '콘솔로 로그인')
        self.assertNotContains(response, 'mdetect_landing_image.png')
        self.assertContains(response, 'Animated cosmetic and shampoo conveyor belt')
        self.assertContains(response, 'initConveyorPicker')
        self.assertContains(response, 'trash-bin')
        self.assertContains(response, 'aria-label="Dashboard로 이동"')
        self.assertContains(response, 'aria-label="메인메뉴로 이동"')
        self.assertContains(response, 'aria-label="빠른 화면 이동"')
        self.assertContains(response, 'class="landing-quick-link"')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("core:dashboard")}"')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("datasets:image_list")}"')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("training:job_list")}"')
        self.assertContains(response, 'aria-label="Image Dataset으로 이동"')
        self.assertContains(response, 'aria-label="Training Jobs로 이동"')
        self.assertContains(response, 'Server-side YOLO inference ready')
        self.assertContains(response, f'href="{reverse("core:manual")}"')
        self.assertContains(response, '>Manual</a>')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("core:dashboard")}"')
        self.assertContains(response, 'href="https://www.thesysm.com"')
        self.assertContains(response, 'src="/static/img/thesysm-logo.png"')
        self.assertContains(response, 'aria-label="theSysm 홈페이지로 이동"')
        self.assertContains(response, f'href="{reverse("datasets:image_upload")}"')
        self.assertContains(response, f'href="{reverse("labeling:workspace")}"')
        self.assertContains(response, f'href="{reverse("datasets:dataset_build")}"')
        self.assertContains(response, f'href="{reverse("training:job_list")}"')
        self.assertContains(response, f'href="{reverse("deployment:android_export")}"')
        self.assertContains(response, f'href="{reverse("deployment:package_list")}"')
        self.assertContains(response, 'aria-label="STEP 01 이미지 준비 화면으로 이동"')
        self.assertContains(response, 'aria-label="STEP 06 스마트폰 적용 화면으로 이동"')
        self.assertContains(response, 'data-th-chat-widget')
        self.assertContains(response, 'floating_chat_button_recycle_ai.png')

    @override_settings(CHAT_WIDGET_ENABLED=False)
    def test_landing_hides_chat_widget_when_disabled(self):
        response = self.client.get(reverse('core:landing'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-th-chat-widget')

    def test_landing_shows_top_auth_controls_for_authenticated_user(self):
        user = get_user_model().objects.create_user(username='landing_user', password='pass')
        self.client.force_login(user)

        response = self.client.get(reverse('core:landing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'landing_user')
        self.assertContains(response, 'action="/accounts/logout/"')
        self.assertContains(response, '>logout</button>')
        self.assertContains(response, f'href="{reverse("core:manual")}"')
        self.assertContains(response, f'href="{reverse("core:dashboard")}"')
        self.assertContains(response, f'href="{reverse("datasets:image_list")}"')
        self.assertContains(response, f'href="{reverse("training:job_list")}"')
        self.assertNotContains(response, f'href="{reverse("login")}?next={reverse("core:dashboard")}"')
        self.assertNotContains(response, '<h2 class="text-2xl font-black">로그인</h2>', html=True)

    def test_investor_briefing_is_public_and_links_to_existing_paths(self):
        response = self.client.get(reverse('core:investor_briefing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Investor Briefing')
        self.assertContains(response, 'InvestorBriefingPage')
        self.assertContains(response, 'Investor Briefing | theDetect Object Detection')
        self.assertContains(response, 'aria-label="Breadcrumb"')
        self.assertContains(response, '<a href="/">theDetect</a>', html=True)
        self.assertContains(response, '<span class="brief-breadcrumb-current" aria-current="page">Investor Briefing</span>', html=True)
        self.assertContains(response, 'data-theme-toggle')
        self.assertContains(response, 'mdetect-theme')
        self.assertContains(response, 'aria-label="빠른 화면 이동"')
        self.assertContains(response, 'class="quick-icon-link"')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("core:dashboard")}"')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("datasets:image_list")}"')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("training:job_list")}"')
        self.assertContains(response, 'class="brief-icon"')
        self.assertContains(response, '◇')
        self.assertContains(response, '▱')
        self.assertContains(response, '제품 이미지 데이터를 현장용 AI 모델로 자동 전환해, 새로운 탐지 서비스를 빠르게 출시할 수 있습니다.')
        self.assertContains(response, '비누각 pink')
        self.assertContains(response, '비누각 white')
        self.assertContains(response, '비누각 mint')
        self.assertContains(response, '샴푸 케이스 white')
        self.assertContains(response, '실제 서비스 화면으로 증명되는 자동화 절차')
        self.assertContains(response, reverse('datasets:object_class_list'))
        self.assertContains(response, reverse('labeling:workspace'))
        self.assertContains(response, reverse('datasets:augmented_dataset_build'))
        self.assertContains(response, reverse('training:job_list'))
        self.assertContains(response, reverse('deployment:android_export'))
        self.assertContains(response, reverse('deployment:package_list'))
        self.assertContains(response, f'href="{reverse("core:demo_walkthrough")}"')
        self.assertContains(response, f'href="{reverse("core:server_detection")}"')
        self.assertNotContains(response, 'PET 병')
        self.assertNotContains(response, '재활용 정보')
        self.assertNotContains(response, '시장 규모')
        self.assertNotContains(response, '정확도')

    def test_demo_walkthrough_is_public_and_links_to_service_start(self):
        response = self.client.get(reverse('core:demo_walkthrough'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo Walkthrough')
        self.assertContains(response, 'DemoWalkthroughPage')
        self.assertContains(response, 'Demo Walkthrough | theDetect Object Detection')
        self.assertContains(response, 'aria-label="Breadcrumb"')
        self.assertContains(response, '<a href="/">theDetect</a>', html=True)
        self.assertContains(response, '<span class="demo-breadcrumb-current" aria-current="page">Demo Walkthrough</span>', html=True)
        self.assertContains(response, 'data-theme-toggle')
        self.assertContains(response, 'mdetect-theme')
        self.assertContains(response, 'aria-label="빠른 화면 이동"')
        self.assertContains(response, 'class="quick-icon-link"')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("core:dashboard")}"')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("datasets:image_list")}"')
        self.assertContains(response, f'href="{reverse("login")}?next={reverse("training:job_list")}"')
        self.assertContains(response, 'class="demo-icon')
        self.assertContains(response, '◇')
        self.assertContains(response, '▱')
        self.assertContains(response, '시연은 제품 탐지 모델이 만들어지고 스마트폰에서 동작하는 순서로 진행됩니다.')
        self.assertContains(response, '서비스 설명 다시 보기')
        self.assertNotContains(response, '투자 설명 다시 보기')
        self.assertContains(response, '전체 시연은 다섯 단계입니다.')
        self.assertContains(response, '발표 시작 멘트')
        self.assertContains(response, '시연 종료 멘트')
        self.assertContains(response, 'STEP 01')
        self.assertContains(response, 'STEP 05')
        self.assertContains(response, f'href="{reverse("datasets:image_upload")}"')
        self.assertContains(response, f'href="{reverse("core:server_detection")}"')
        self.assertContains(response, f'href="{reverse("datasets:object_class_list")}"')
        self.assertContains(response, f'href="{reverse("deployment:package_list")}"')
        self.assertContains(response, f'href="{reverse("core:investor_briefing")}"')
        self.assertNotContains(response, 'PET 병')
        self.assertNotContains(response, '재활용 안내')
        self.assertNotContains(response, '수거')
        self.assertNotContains(response, '정확도')
        self.assertNotContains(response, '처리 시간')
        self.assertNotContains(response, '절감률')

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
        self.assertContains(response, 'Investor Briefing')
        self.assertContains(response, 'Demo Walkthrough')
        self.assertContains(response, reverse('core:investor_briefing'))
        self.assertContains(response, reverse('core:demo_walkthrough'))
        self.assertContains(response, reverse('core:server_detection'))
        self.assertContains(response, 'showNavigation')
        self.assertContains(response, 'hideNavigation')
        self.assertContains(response, 'data-nav-open-button')
        self.assertContains(response, 'data-nav-show-icon')
        self.assertContains(response, 'data-nav-hide-icon')
        self.assertContains(response, '-&gt;')
        self.assertContains(response, '&lt;-')
        self.assertContains(response, 'data-navigation-sidebar')
        self.assertContains(response, 'data-nav-backdrop')
        self.assertContains(response, "classList.toggle('sidebar-collapsed', collapsed)")
        self.assertContains(response, '.app-sidebar.sidebar-collapsed { width: 3.75rem !important; transform: none; }')
        self.assertContains(response, '.content-shell.sidebar-collapsed { padding-left: 3.75rem !important; }')
        self.assertContains(response, 'href="/"')
        self.assertContains(response, 'aria-label="Breadcrumb"')
        self.assertContains(response, '<span class="shrink-0 text-slate-400" aria-hidden="true">/</span>', html=True)
        self.assertContains(response, 'dashboard_user')
        self.assertContains(response, 'action="/accounts/logout/"')
        self.assertContains(response, 'href="https://www.thesysm.com"')
        self.assertContains(response, 'src="/static/img/thesysm-logo.png"')
        self.assertContains(response, 'aria-label="theSysm 홈페이지로 이동"')
        self.assertContains(response, '>logout</button>')
        self.assertNotContains(response, 'Service URL')
        self.assertNotContains(response, 'Django Admin')

    def test_dashboard_shows_django_admin_link_for_superuser(self):
        user = get_user_model().objects.create_superuser(username='dashboard_admin', password='pass')
        self.client.force_login(user)

        response = self.client.get(reverse('core:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Admin')
        self.assertContains(response, reverse('admin:index'))
        self.assertContains(response, 'data-th-chat-widget')


class LlamaChatTests(TestCase):
    def test_llama_chat_returns_reply_and_model(self):
        with patch('core.views.build_chat_response', return_value={
            'ok': True,
            'reply': 'Manual 기준으로 Dataset Build를 먼저 실행하세요.',
            'model': 'test-model',
        }) as mocked:
            response = self.client.post(
                reverse('core:llama_chat'),
                data=json.dumps({
                    'message': '이 페이지의 사용법을 알려줘',
                    'history': [],
                    'page': {
                        'path': '/datasets/build/',
                        'title': 'Dataset Build',
                        'headings': ['Dataset Build'],
                        'visible_text': 'Dataset Build Train ratio Val ratio',
                    },
                }),
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reply'], 'Manual 기준으로 Dataset Build를 먼저 실행하세요.')
        mocked.assert_called_once()
        self.assertEqual(mocked.call_args.kwargs['page']['path'], '/datasets/build/')

    @override_settings(CHAT_WIDGET_ENABLED=False)
    def test_llama_chat_disabled_returns_json_error(self):
        response = self.client.post(
            reverse('core:llama_chat'),
            data=json.dumps({'message': '안녕'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()['ok'])

    def test_llama_chat_rejects_empty_message(self):
        response = self.client.post(
            reverse('core:llama_chat'),
            data=json.dumps({'message': '   '}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    @override_settings(CHAT_MESSAGE_MAX_LENGTH=5)
    def test_llama_chat_rejects_too_long_message(self):
        response = self.client.post(
            reverse('core:llama_chat'),
            data=json.dumps({'message': '123456'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    def test_history_ignores_system_role_and_keeps_recent_messages(self):
        history = normalize_history([
            {'role': 'system', 'content': 'ignore'},
            {'role': 'user', 'content': 'one'},
            {'role': 'assistant', 'content': 'two'},
        ])

        self.assertEqual(history, [
            {'role': 'user', 'content': 'one'},
            {'role': 'assistant', 'content': 'two'},
        ])

    def test_manual_context_uses_project_docs(self):
        context = build_manual_context('Android Model Update 모델 다운로드', {'path': '/models/android/packages/'})

        self.assertIn('Android', context)

    def test_page_context_is_normalized_and_added_to_prompt(self):
        page = normalize_page_context({
            'url': 'https://detect.thesysm.com/dashboard/?x=1',
            'path': '/dashboard/?x=1',
            'title': 'Dashboard',
            'headings': ['Dashboard', 'Server Core Status'],
            'visible_text': 'Object Classes Uploaded Images Dataset Versions',
            'ignored': '<script>',
        })

        self.assertEqual(page['path'], '/dashboard/')
        prompt = build_system_prompt('이 페이지의 사용법을 알려줘', page)
        self.assertIn('현재 URL path: /dashboard/', prompt)
        self.assertIn('Dashboard', prompt)
        self.assertIn('이 페이지', prompt)

    def test_page_hints_for_known_paths(self):
        hints = page_hints_for_path('/training/jobs/123/')

        self.assertIn('training jobs', hints)

    def test_dashboard_shows_django_admin_link_for_staff_user(self):
        user = get_user_model().objects.create_user(username='dashboard_staff', password='pass', is_staff=True)
        self.client.force_login(user)

        response = self.client.get(reverse('core:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Admin')
        self.assertContains(response, reverse('admin:index'))


class ManualTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='manual_user', password='pass')
        self.staff_user = get_user_model().objects.create_user(username='manual_staff', password='pass', is_staff=True)

    def test_manual_home_is_public(self):
        response = self.client.get(reverse('core:manual'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/manual/view/', response['Location'])

    def test_manual_menu_is_visible_on_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manual')
        self.assertContains(response, reverse('core:manual'))

    def test_manual_home_redirects_to_first_document(self):
        response = self.client.get(reverse('core:manual'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/manual/view/', response['Location'])

    def test_manual_view_renders_document(self):
        response = self.client.get(reverse('core:manual_view', kwargs={'doc_path': 'README.md'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Operations Manual')
        self.assertContains(response, 'README')

    def test_manual_raw_view_returns_text(self):
        response = self.client.get(reverse('core:manual_raw', kwargs={'doc_path': 'README.md'}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')

    def test_manual_search_renders_results(self):
        response = self.client.get(reverse('core:manual_view', kwargs={'doc_path': 'README.md'}), {'q': 'Django'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '검색 결과')

    def test_manual_shows_apk_download_for_public_users(self):
        release = SimpleNamespace(
            title='MDetect',
            version='1.0.0 (1)',
            variant='debug',
            original_filename='app-debug.apk',
            size_label='49 MB',
            created_at=timezone.now(),
            timezone_label='KST',
            notes='Latest locally built Android APK.',
        )

        with patch('core.manual_services.latest_apk_releases', return_value=[release]):
            response = self.client.get(reverse('core:manual_view', kwargs={'doc_path': 'README.md'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'APK 배포 파일')
        self.assertContains(response, 'Android 앱을 설치한 뒤 앱에서 회원가입을 진행할 수 있습니다.')
        self.assertContains(response, 'app-debug.apk')
        self.assertContains(response, 'KST')
        self.assertContains(response, reverse('core:manual_apk_download'))

    def test_manual_shows_apk_download_for_non_staff_users(self):
        release = SimpleNamespace(
            title='MDetect',
            version='1.0.0 (1)',
            variant='debug',
            original_filename='app-debug.apk',
            size_label='49 MB',
            created_at=timezone.now(),
            timezone_label='KST',
            notes='Latest locally built Android APK.',
        )

        with patch('core.manual_services.latest_apk_releases', return_value=[release]):
            response = self.client.get(reverse('core:manual_view', kwargs={'doc_path': 'README.md'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'APK 배포 파일')
        self.assertContains(response, reverse('core:manual_apk_download'))

    def test_manual_apk_download_public_access_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            apk_path = Path(tmpdir) / 'app-debug.apk'
            apk_path.write_bytes(b'apk-binary-data')
            release = SimpleNamespace(
                path=apk_path,
                download_filename='mdetect-debug-1_0_0.apk',
            )

            with patch('core.manual_services.latest_apk_releases', return_value=[release]):
                response = self.client.get(reverse('core:manual_apk_download'))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/vnd.android.package-archive')
            self.assertIn('attachment; filename="mdetect-debug-1_0_0.apk"', response['Content-Disposition'])
            self.assertEqual(b''.join(response.streaming_content), b'apk-binary-data')

    def test_latest_apk_release_time_uses_current_timezone(self):
        with tempfile.TemporaryDirectory() as tmpdir, timezone.override('Asia/Seoul'):
            apk_root = Path(tmpdir)
            apk_path = apk_root / 'debug' / 'app-debug.apk'
            apk_path.parent.mkdir(parents=True)
            apk_path.write_bytes(b'apk')
            timestamp = timezone.datetime(2026, 6, 14, 6, 11, 23, tzinfo=datetime_timezone.utc).timestamp()
            os.utime(apk_path, (timestamp, timestamp))

            with patch('core.manual_services.android_apk_outputs_root', return_value=apk_root):
                releases = manual_services.latest_apk_releases()

        self.assertEqual(len(releases), 1)
        self.assertEqual(releases[0].created_at.strftime('%Y-%m-%d %H:%M:%S'), '2026-06-14 15:11:23')
        self.assertEqual(releases[0].timezone_label, 'KST')


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


class DetectionLogScreenTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='log_user', password='pass')

    def test_detection_logs_requires_login(self):
        response = self.client.get(reverse('core:detection_logs'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_detection_logs_screen_lists_recent_logs(self):
        DetectionLog.objects.create(
            mode=DetectionLog.Mode.SERVER,
            model_version='screen_model',
            top_class='soap_case_pink',
            top_confidence=0.91,
            processing_time_ms=123,
            device_info='test-device',
            user=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:detection_logs'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recent detection logs')
        self.assertContains(response, 'screen_model')
        self.assertContains(response, 'soap_case_pink')
        self.assertContains(response, 'test-device')


class ProjectSettingsScreenTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='settings_user', password='pass')

    def test_project_settings_requires_login(self):
        response = self.client.get(reverse('core:project_settings'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_project_settings_screen_returns_200_without_models(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:project_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Project Settings')
        self.assertContains(response, 'Read-only overview of current theDetect system settings')
        self.assertContains(response, 'No active server model')
        self.assertContains(response, 'No deployed Android model package')

    def test_project_settings_context_contains_data_summary(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:project_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('data_summary', response.context)
        self.assertIn('ObjectClass count', response.context['data_summary'])
        self.assertIn('DetectionLog count', response.context['data_summary'])

    def test_project_settings_system_checks_are_displayed(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:project_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'System Checks')
        self.assertContains(response, 'PROJECT_DATA_DIR exists')
