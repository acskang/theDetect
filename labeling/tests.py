import json
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from datasets.models import ObjectClass, UploadedImage

from .models import LabelBox


def make_image_file(name='label.png', size=(100, 80)):
    buffer = BytesIO()
    Image.new('RGB', size, color='blue').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class LabelingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='labeler', password='pass')
        self.client.force_login(self.user)
        self.object_class = ObjectClass.objects.create(
            name='box_class',
            display_name='Box Class',
            color='#2563eb',
            is_active=True,
        )
        self.image = UploadedImage.objects.create(
            file=make_image_file(),
            original_filename='label.png',
            width=100,
            height=80,
            file_size=123,
            upload_source=UploadedImage.UploadSource.MULTI,
            uploaded_by=self.user,
        )

    def test_label_box_model_creation(self):
        box = LabelBox.objects.create(
            image=self.image,
            object_class=self.object_class,
            x_min=10,
            y_min=12,
            x_max=40,
            y_max=50,
            image_width=100,
            image_height=80,
            created_by=self.user,
        )

        self.assertEqual(box.image, self.image)
        self.assertEqual(box.object_class, self.object_class)

    def test_invalid_coordinates_are_rejected(self):
        response = self.client.post(
            f'/labeling/images/{self.image.id}/boxes/save/',
            data=json.dumps({
                'boxes': [{
                    'object_class_id': self.object_class.id,
                    'x_min': 90,
                    'y_min': 10,
                    'x_max': 120,
                    'y_max': 30,
                }]
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(LabelBox.objects.count(), 0)

    def test_workspace_list_returns_200(self):
        response = self.client.get('/labeling/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Labeling Workspace')
        self.assertContains(response, 'Step 1. Auto rough boxes')
        self.assertContains(response, 'Step 2. Duplicate previous box')
        self.assertContains(response, 'Step 3. Active model pre-label')

    def test_workspace_class_tab_filters_images(self):
        other_class = ObjectClass.objects.create(
            name='other_class',
            display_name='Other Class',
            color='#9ca3af',
            is_active=True,
            sort_order=20,
        )
        self.image.hint_class = self.object_class
        self.image.save(update_fields=['hint_class'])
        other_image = UploadedImage.objects.create(
            file=make_image_file('other.png'),
            original_filename='other.png',
            width=100,
            height=80,
            file_size=456,
            upload_source=UploadedImage.UploadSource.MULTI,
            uploaded_by=self.user,
            hint_class=other_class,
        )

        response = self.client.get(f'/labeling/?class={self.object_class.id}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.image.original_filename)
        self.assertNotContains(response, other_image.original_filename)
        self.assertContains(response, 'Box Class')

    def test_auto_rough_boxes_creates_draft_box(self):
        response = self.client.post('/labeling/auto/rough-boxes/', {'object_class_id': self.object_class.id})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(LabelBox.objects.count(), 1)
        box = LabelBox.objects.get()
        self.assertEqual(box.object_class, self.object_class)
        self.assertEqual((box.x_min, box.y_min, box.x_max, box.y_max), (18, 18, 82, 62))
        self.image.refresh_from_db()
        self.assertEqual(self.image.status, UploadedImage.Status.LABELING)

    def test_auto_rough_boxes_can_scope_to_class_tab(self):
        other_class = ObjectClass.objects.create(
            name='other_class',
            display_name='Other Class',
            color='#9ca3af',
            is_active=True,
            sort_order=20,
        )
        self.image.hint_class = self.object_class
        self.image.save(update_fields=['hint_class'])
        other_image = UploadedImage.objects.create(
            file=make_image_file('other.png'),
            original_filename='other.png',
            width=100,
            height=80,
            file_size=456,
            upload_source=UploadedImage.UploadSource.MULTI,
            uploaded_by=self.user,
            hint_class=other_class,
        )

        response = self.client.post(
            '/labeling/auto/rough-boxes/',
            {'object_class_id': self.object_class.id, 'scope_class_id': self.object_class.id},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(LabelBox.objects.count(), 1)
        self.assertTrue(LabelBox.objects.filter(image=self.image, object_class=self.object_class).exists())
        self.assertFalse(LabelBox.objects.filter(image=other_image).exists())

    def test_duplicate_previous_boxes_copies_to_empty_images(self):
        LabelBox.objects.create(
            image=self.image,
            object_class=self.object_class,
            x_min=10,
            y_min=10,
            x_max=50,
            y_max=40,
            image_width=100,
            image_height=80,
            created_by=self.user,
        )
        target = UploadedImage.objects.create(
            file=make_image_file('target.png', size=(200, 160)),
            original_filename='target.png',
            width=200,
            height=160,
            file_size=456,
            upload_source=UploadedImage.UploadSource.MULTI,
            uploaded_by=self.user,
        )

        response = self.client.post('/labeling/auto/duplicate-previous/')

        self.assertEqual(response.status_code, 302)
        copied_box = LabelBox.objects.get(image=target)
        self.assertEqual((copied_box.x_min, copied_box.y_min, copied_box.x_max, copied_box.y_max), (20, 20, 100, 80))
        target.refresh_from_db()
        self.assertEqual(target.status, UploadedImage.Status.LABELING)

    def test_auto_label_active_model_without_active_model_does_not_create_boxes(self):
        response = self.client.post('/labeling/auto/active-model/', {'confidence': '0.35'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(LabelBox.objects.count(), 0)

    def test_editor_returns_200(self):
        response = self.client.get(f'/labeling/images/{self.image.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.image.original_filename)
        self.assertContains(response, 'data-label-stage')
        self.assertContains(response, 'data-add-rough-box')
        self.assertContains(response, 'Add rough box')
        self.assertContains(response, 'data-save-boxes')
        self.assertContains(response, 'setPointerCapture')
        self.assertContains(response, 'data-resize-corner="tl"')
        self.assertContains(response, 'data-resize-corner="br"')
        self.assertContains(response, 'resizeBox(box, point')
        self.assertContains(response, "stage.addEventListener('pointerdown'")
        self.assertContains(response, 'inside: rawX >= 0')
        self.assertNotContains(response, 'Mark labeled')

    def test_next_image_respects_class_tab(self):
        other_class = ObjectClass.objects.create(
            name='other_class',
            display_name='Other Class',
            color='#9ca3af',
            is_active=True,
            sort_order=20,
        )
        self.image.hint_class = self.object_class
        self.image.save(update_fields=['hint_class'])
        next_same_class = UploadedImage.objects.create(
            file=make_image_file('next.png'),
            original_filename='next.png',
            width=100,
            height=80,
            file_size=456,
            upload_source=UploadedImage.UploadSource.MULTI,
            uploaded_by=self.user,
            hint_class=self.object_class,
        )
        UploadedImage.objects.create(
            file=make_image_file('other.png'),
            original_filename='other.png',
            width=100,
            height=80,
            file_size=456,
            upload_source=UploadedImage.UploadSource.MULTI,
            uploaded_by=self.user,
            hint_class=other_class,
        )

        response = self.client.get(f'/labeling/images/{self.image.id}/next/?class={self.object_class.id}')

        self.assertRedirects(
            response,
            f'/labeling/images/{next_same_class.id}/?class={self.object_class.id}',
            fetch_redirect_response=False,
        )

    def test_save_boxes_api_replaces_boxes_and_updates_status(self):
        response = self.client.post(
            f'/labeling/images/{self.image.id}/boxes/save/',
            data=json.dumps({
                'boxes': [{
                    'object_class_id': self.object_class.id,
                    'x_min': 10,
                    'y_min': 12,
                    'x_max': 40,
                    'y_max': 50,
                }]
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'saved': True, 'count': 1})
        self.assertEqual(LabelBox.objects.count(), 1)
        self.image.refresh_from_db()
        self.assertEqual(self.image.status, UploadedImage.Status.LABELED)
