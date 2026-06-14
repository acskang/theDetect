import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import AccountProfile, normalize_phone_number


class Command(BaseCommand):
    help = 'Create or update the MVP test user from environment variables.'

    def handle(self, *args, **options):
        username = os.environ.get('MDETECT_TEST_USERNAME')
        password = os.environ.get('MDETECT_TEST_PASSWORD')
        if not username or not password:
            raise CommandError('Set MDETECT_TEST_USERNAME and MDETECT_TEST_PASSWORD.')

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_active = True
        user.save()

        phone_number = normalize_phone_number(os.environ.get('MDETECT_TEST_PHONE', ''))
        if phone_number:
            AccountProfile.objects.update_or_create(
                user=user,
                defaults={'phone_number': phone_number},
            )

        action = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(f'MVP test user {action}: {username}'))
