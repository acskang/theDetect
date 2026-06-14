from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.test import override_settings

from .models import AccountProfile


class AccountSignupTests(TestCase):
    def test_signup_page_responds_200(self):
        response = self.client.get(reverse('accounts:signup'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phone number')

    def test_signup_requires_phone_number(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'no_phone',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        self.assertFalse(get_user_model().objects.filter(username='no_phone').exists())

    def test_signup_creates_user_profile_with_normalized_phone(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'phone_user',
            'phone_number': '010-1234-5678',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username='phone_user')
        self.assertEqual(AccountProfile.objects.get(user=user).phone_number, '01012345678')

    def test_signup_allows_temporary_weak_password(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'weak_password_user',
            'phone_number': '010-2222-3333',
            'password1': '1234',
            'password2': '1234',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username='weak_password_user').exists())

    def test_login_page_responds_200(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username or phone number')

    @override_settings()
    def test_ensure_mvp_test_user_creates_approved_profile(self):
        import os
        original = {
            'MDETECT_TEST_USERNAME': os.environ.get('MDETECT_TEST_USERNAME'),
            'MDETECT_TEST_PASSWORD': os.environ.get('MDETECT_TEST_PASSWORD'),
            'MDETECT_TEST_PHONE': os.environ.get('MDETECT_TEST_PHONE'),
        }
        os.environ['MDETECT_TEST_USERNAME'] = 'mdetect_smoke_test'
        os.environ['MDETECT_TEST_PASSWORD'] = 'StrongPass123!'
        os.environ['MDETECT_TEST_PHONE'] = '010-0000-1111'
        try:
            call_command('ensure_mvp_test_user', verbosity=0)
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        user = get_user_model().objects.get(username='mdetect_smoke_test')
        profile = AccountProfile.objects.get(user=user)
        self.assertEqual(profile.phone_number, '01000001111')
        self.assertEqual(profile.approval_status, AccountProfile.ApprovalStatus.APPROVED)
