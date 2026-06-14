import tempfile
from io import BytesIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), PROJECT_DATA_DIR=tempfile.mkdtemp())
class SmokeServerDetectCommandTests(TestCase):
    def test_command_reports_no_active_model_without_error(self):
        buffer = BytesIO()
        Image.new('RGB', (16, 12), color='black').save(buffer, format='JPEG')
        image_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image_path.write(buffer.getvalue())
        image_path.close()
        output = BytesIO()

        text_output = tempfile.SpooledTemporaryFile(mode='w+t')
        call_command('smoke_server_detect', '--image', image_path.name, stdout=text_output)
        text_output.seek(0)

        self.assertIn('model_available=false', text_output.read())
