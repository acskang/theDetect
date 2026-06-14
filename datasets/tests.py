import tempfile
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from unittest.mock import patch
from PIL import Image

from labeling.models import LabelBox

from .augmentation import deferred_augmentation_names, implemented_augmentation_names
from .forms import AugmentedDatasetBuildForm, DatasetBuildForm
from .models import DatasetVersion, ObjectClass, UploadedImage
from .yolo_builder import build_dataset_version, yolo_box_coordinates


def image_bytes():
    buffer = BytesIO()
    Image.new('RGB', (12, 8), color='red').save(buffer, format='PNG')
    return buffer.getvalue()


def image_bytes_with_size(size):
    buffer = BytesIO()
    Image.new('RGB', size, color='red').save(buffer, format='JPEG')
    return buffer.getvalue()


class ImageUploadTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='uploader', password='pass')
        self.client.force_login(self.user)
        self.hint_class, _ = ObjectClass.objects.get_or_create(name='class_01', defaults={'display_name': 'class_01'})

    def test_multi_image_upload_creates_uploaded_image(self):
        response = self.client.post(
            '/datasets/images/upload/',
            {
                'images': [
                    SimpleUploadedFile('sample.png', image_bytes(), content_type='image/png'),
                ],
            },
        )

        self.assertEqual(response.status_code, 302)
        uploaded = UploadedImage.objects.get()
        self.assertEqual(uploaded.original_filename, 'sample.png')
        self.assertEqual(uploaded.width, 12)
        self.assertEqual(uploaded.height, 8)
        self.assertEqual(uploaded.upload_source, UploadedImage.UploadSource.MULTI)
        self.assertTrue(uploaded.file.name.endswith('.jpg'))

    def test_image_upload_screen_has_object_class_selector(self):
        response = self.client.get(f'/datasets/images/upload/?class={self.hint_class.id}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Object class')
        self.assertContains(response, f'value="{self.hint_class.id}" selected')

    def test_multi_image_upload_can_save_selected_class_hint(self):
        response = self.client.post(
            '/datasets/images/upload/',
            {
                'object_class': str(self.hint_class.id),
                'images': [
                    SimpleUploadedFile('sample.png', image_bytes(), content_type='image/png'),
                ],
            },
        )

        self.assertRedirects(response, f'/datasets/images/?class={self.hint_class.id}', fetch_redirect_response=False)
        uploaded = UploadedImage.objects.get()
        self.assertEqual(uploaded.hint_class, self.hint_class)

    @override_settings(MDETECT_MAX_IMAGE_LONG_EDGE=1280)
    def test_large_multi_image_upload_resizes_long_edge(self):
        response = self.client.post(
            '/datasets/images/upload/',
            {
                'images': [
                    SimpleUploadedFile('large.jpg', image_bytes_with_size((4032, 2268)), content_type='image/jpeg'),
                ],
            },
        )

        self.assertEqual(response.status_code, 302)
        uploaded = UploadedImage.objects.get()
        self.assertEqual(uploaded.width, 1280)
        self.assertEqual(uploaded.height, 720)
        with Image.open(uploaded.file.path) as stored:
            self.assertEqual(stored.size, (1280, 720))
            self.assertEqual(stored.format, 'JPEG')

    def test_zip_upload_imports_safe_images_and_skips_traversal(self):
        buffer = BytesIO()
        with ZipFile(buffer, 'w') as archive:
            archive.writestr('class_01/safe.png', image_bytes())
            archive.writestr('../unsafe.png', image_bytes())
            archive.writestr('notes.txt', 'ignore me')
        buffer.seek(0)

        response = self.client.post(
            '/datasets/images/upload/',
            {
                'zip_file': SimpleUploadedFile('dataset.zip', buffer.read(), content_type='application/zip'),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedImage.objects.count(), 1)
        uploaded = UploadedImage.objects.get()
        self.assertEqual(uploaded.upload_source, UploadedImage.UploadSource.ZIP)
        self.assertEqual(uploaded.hint_class, self.hint_class)

    def test_zip_upload_selected_class_overrides_folder_hint(self):
        selected_class = ObjectClass.objects.create(name='selected_class', display_name='Selected Class')
        buffer = BytesIO()
        with ZipFile(buffer, 'w') as archive:
            archive.writestr('class_01/safe.png', image_bytes())
        buffer.seek(0)

        response = self.client.post(
            '/datasets/images/upload/',
            {
                'object_class': str(selected_class.id),
                'zip_file': SimpleUploadedFile('dataset.zip', buffer.read(), content_type='application/zip'),
            },
        )

        self.assertRedirects(response, f'/datasets/images/?class={selected_class.id}', fetch_redirect_response=False)
        uploaded = UploadedImage.objects.get()
        self.assertEqual(uploaded.upload_source, UploadedImage.UploadSource.ZIP)
        self.assertEqual(uploaded.hint_class, selected_class)

    @override_settings(MDETECT_MAX_IMAGE_LONG_EDGE=1280)
    def test_zip_upload_resizes_large_image(self):
        buffer = BytesIO()
        with ZipFile(buffer, 'w') as archive:
            archive.writestr('class_01/large.jpg', image_bytes_with_size((3000, 4000)))
        buffer.seek(0)

        response = self.client.post(
            '/datasets/images/upload/',
            {
                'zip_file': SimpleUploadedFile('dataset.zip', buffer.read(), content_type='application/zip'),
            },
        )

        self.assertEqual(response.status_code, 302)
        uploaded = UploadedImage.objects.get()
        self.assertEqual(uploaded.width, 960)
        self.assertEqual(uploaded.height, 1280)

    def test_image_list_has_bulk_delete_controls(self):
        UploadedImage.objects.create(
            file=SimpleUploadedFile('listed.png', image_bytes(), content_type='image/png'),
            original_filename='listed.png',
            width=12,
            height=8,
            file_size=10,
            upload_source=UploadedImage.UploadSource.MANUAL,
            uploaded_by=self.user,
        )

        response = self.client.get('/datasets/images/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete selected')
        self.assertContains(response, 'data-select-all-images')
        self.assertContains(response, 'name="image_ids"')
        self.assertContains(response, '/datasets/images/bulk-delete/')

    def test_image_list_can_filter_by_object_class(self):
        other_class = ObjectClass.objects.create(name='other_class', display_name='Other Class')
        UploadedImage.objects.create(
            file=SimpleUploadedFile('selected.png', image_bytes(), content_type='image/png'),
            original_filename='selected.png',
            width=12,
            height=8,
            file_size=10,
            upload_source=UploadedImage.UploadSource.MANUAL,
            uploaded_by=self.user,
            hint_class=self.hint_class,
        )
        UploadedImage.objects.create(
            file=SimpleUploadedFile('other.png', image_bytes(), content_type='image/png'),
            original_filename='other.png',
            width=12,
            height=8,
            file_size=10,
            upload_source=UploadedImage.UploadSource.MANUAL,
            uploaded_by=self.user,
            hint_class=other_class,
        )

        response = self.client.get(f'/datasets/images/?class={self.hint_class.id}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'selected.png')
        self.assertNotContains(response, 'other.png')
        self.assertContains(response, 'class_01')

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_image_delete_removes_record_file_and_labels(self):
        uploaded = UploadedImage.objects.create(
            file=SimpleUploadedFile('delete-me.png', image_bytes(), content_type='image/png'),
            original_filename='delete-me.png',
            width=12,
            height=8,
            file_size=10,
            upload_source=UploadedImage.UploadSource.MANUAL,
            status=UploadedImage.Status.LABELING,
            uploaded_by=self.user,
        )
        LabelBox.objects.create(
            image=uploaded,
            object_class=self.hint_class,
            x_min=1,
            y_min=1,
            x_max=8,
            y_max=6,
            image_width=12,
            image_height=8,
            created_by=self.user,
        )
        file_path = Path(uploaded.file.path)
        self.assertTrue(file_path.exists())

        response = self.client.post(f'/datasets/images/{uploaded.id}/delete/')

        self.assertEqual(response.status_code, 302)
        self.assertFalse(UploadedImage.objects.filter(id=uploaded.id).exists())
        self.assertEqual(LabelBox.objects.count(), 0)
        self.assertFalse(file_path.exists())

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_image_bulk_delete_removes_selected_records_files_and_labels(self):
        selected_images = []
        selected_paths = []
        for index in range(2):
            image = UploadedImage.objects.create(
                file=SimpleUploadedFile(f'selected-{index}.png', image_bytes(), content_type='image/png'),
                original_filename=f'selected-{index}.png',
                width=12,
                height=8,
                file_size=10,
                upload_source=UploadedImage.UploadSource.MANUAL,
                status=UploadedImage.Status.LABELING,
                uploaded_by=self.user,
            )
            LabelBox.objects.create(
                image=image,
                object_class=self.hint_class,
                x_min=1,
                y_min=1,
                x_max=8,
                y_max=6,
                image_width=12,
                image_height=8,
                created_by=self.user,
            )
            selected_images.append(image)
            selected_paths.append(Path(image.file.path))
        kept_image = UploadedImage.objects.create(
            file=SimpleUploadedFile('kept.png', image_bytes(), content_type='image/png'),
            original_filename='kept.png',
            width=12,
            height=8,
            file_size=10,
            upload_source=UploadedImage.UploadSource.MANUAL,
            uploaded_by=self.user,
        )

        response = self.client.post(
            '/datasets/images/bulk-delete/',
            {'image_ids': [str(image.id) for image in selected_images]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(UploadedImage.objects.filter(id__in=[image.id for image in selected_images]).exists())
        self.assertTrue(UploadedImage.objects.filter(id=kept_image.id).exists())
        self.assertEqual(LabelBox.objects.count(), 0)
        for path in selected_paths:
            self.assertFalse(path.exists())


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), PROJECT_DATA_DIR=tempfile.mkdtemp())
class DatasetBuildTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='builder', password='pass')
        self.object_class = ObjectClass.objects.create(name='build_class', display_name='Build Class', sort_order=1)
        self.image = UploadedImage.objects.create(
            file=SimpleUploadedFile('build.png', image_bytes(), content_type='image/png'),
            original_filename='build.png',
            width=12,
            height=8,
            file_size=10,
            upload_source=UploadedImage.UploadSource.MANUAL,
            status=UploadedImage.Status.LABELED,
            uploaded_by=self.user,
        )
        self.box = LabelBox.objects.create(
            image=self.image,
            object_class=self.object_class,
            x_min=3,
            y_min=2,
            x_max=9,
            y_max=6,
            image_width=12,
            image_height=8,
            created_by=self.user,
        )

    def test_yolo_coordinate_conversion(self):
        self.assertEqual(yolo_box_coordinates(self.box), (0.5, 0.5, 0.5, 0.5))

    def test_dataset_build_creates_yolo_files_and_data_yaml(self):
        form = DatasetBuildForm(data={
            'name': 'dataset_one',
            'description': 'test dataset',
            'train_ratio': 80,
            'val_ratio': 10,
            'test_ratio': 10,
            'random_seed': 42,
            'include_only_labeled_images': 'on',
            'exclude_invalid_boxes': 'on',
            'build_memo': 'memo',
        })
        self.assertTrue(form.is_valid(), form.errors)

        dataset = build_dataset_version(form, user=self.user)

        self.assertEqual(dataset.status, DatasetVersion.Status.BUILT)
        self.assertEqual(dataset.build_config_json.get('build_type'), 'original')
        self.assertFalse(dataset.build_config_json.get('use_augmentation', False))
        self.assertEqual(dataset.class_summary_json['image_count'], 1)
        self.assertTrue((Path(dataset.output_path) / 'data.yaml').exists())
        data_yaml = (Path(dataset.output_path) / 'data.yaml').read_text(encoding='utf-8')
        self.assertIn('train: images/train', data_yaml)
        self.assertIn('names:', data_yaml)

    def test_augmented_dataset_build_creates_target_count_and_yolo_labels(self):
        form = AugmentedDatasetBuildForm(data={
            'name': 'dataset_augmented',
            'description': 'augmented dataset',
            'train_ratio': 80,
            'val_ratio': 10,
            'test_ratio': 10,
            'random_seed': 7,
            'include_only_labeled_images': 'on',
            'exclude_invalid_boxes': 'on',
            'build_memo': 'memo',
            'target_images_per_class': 4,
            'max_augmentations_per_source_image': 5,
            'color_safe_augmentation': 'on',
        })
        self.assertTrue(form.is_valid(), form.errors)

        dataset = build_dataset_version(form, user=self.user, use_augmentation=True)

        self.assertEqual(dataset.status, DatasetVersion.Status.BUILT)
        self.assertEqual(dataset.build_config_json['build_type'], 'augmented')
        self.assertTrue(dataset.build_config_json['use_augmentation'])
        self.assertGreaterEqual(dataset.class_summary_json['image_count'], 4)
        self.assertGreaterEqual(dataset.class_summary_json['augmented_image_count'], 3)
        labels = list((Path(dataset.output_path) / 'labels').glob('*/*.txt'))
        self.assertTrue(labels)
        for label in labels:
            for line in label.read_text(encoding='utf-8').splitlines():
                parts = line.split()
                self.assertEqual(len(parts), 5)
                for value in parts[1:]:
                    self.assertGreaterEqual(float(value), 0)
                    self.assertLessEqual(float(value), 1)

    def test_augmented_dataset_build_keeps_source_augments_in_same_split(self):
        for index in range(1, 3):
            image = UploadedImage.objects.create(
                file=SimpleUploadedFile(f'build-{index}.png', image_bytes(), content_type='image/png'),
                original_filename=f'build-{index}.png',
                width=12,
                height=8,
                file_size=10,
                upload_source=UploadedImage.UploadSource.MANUAL,
                status=UploadedImage.Status.LABELED,
                uploaded_by=self.user,
            )
            LabelBox.objects.create(
                image=image,
                object_class=self.object_class,
                x_min=3,
                y_min=2,
                x_max=9,
                y_max=6,
                image_width=12,
                image_height=8,
                created_by=self.user,
            )
        form = AugmentedDatasetBuildForm(data={
            'name': 'dataset_augmented_split',
            'description': 'augmented split dataset',
            'train_ratio': 34,
            'val_ratio': 33,
            'test_ratio': 33,
            'random_seed': 3,
            'include_only_labeled_images': 'on',
            'exclude_invalid_boxes': 'on',
            'target_images_per_class': 6,
            'max_augmentations_per_source_image': 3,
            'color_safe_augmentation': 'on',
        })
        self.assertTrue(form.is_valid(), form.errors)

        dataset = build_dataset_version(form, user=self.user, use_augmentation=True)
        source_splits = dataset.class_summary_json['source_image_splits']
        images_root = Path(dataset.output_path) / 'images'

        for image in UploadedImage.objects.filter(id__in=source_splits.keys()):
            expected_split = source_splits[str(image.id)] if str(image.id) in source_splits else source_splits[image.id]
            source_stem = Path(image.file.name).stem
            for split in ('train', 'val', 'test'):
                for augmented in (images_root / split).glob(f'*_{source_stem}_aug*.jpg'):
                    self.assertEqual(split, expected_split)

    def test_color_safe_augmentation_policy_does_not_include_hue_or_saturation(self):
        self.assertIn('brightness', implemented_augmentation_names())
        self.assertIn('contrast', implemented_augmentation_names())
        self.assertIn('hue_shift', deferred_augmentation_names())
        self.assertIn('saturation_shift', deferred_augmentation_names())
        self.assertNotIn('hue_shift', implemented_augmentation_names())
        self.assertNotIn('saturation_shift', implemented_augmentation_names())

    def test_dataset_build_screen_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get('/datasets/build/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Build DatasetVersion')
        self.assertNotContains(response, 'Use augmentation')
        self.assertNotContains(response, 'Target images per class')
        self.assertNotContains(response, 'Max augmentations per source image')
        self.assertNotContains(response, 'Color-safe augmentation')

    def test_dataset_build_post_saves_original_build_type(self):
        self.client.force_login(self.user)
        response = self.client.post('/datasets/build/', {
            'name': 'dataset_original_post',
            'description': 'test dataset',
            'train_ratio': 80,
            'val_ratio': 10,
            'test_ratio': 10,
            'random_seed': 42,
            'include_only_labeled_images': 'on',
            'exclude_invalid_boxes': 'on',
            'build_memo': 'memo',
        })

        self.assertEqual(response.status_code, 302)
        dataset = DatasetVersion.objects.get(name='dataset_original_post')
        self.assertEqual(dataset.build_config_json['build_type'], 'original')
        self.assertFalse(dataset.build_config_json['use_augmentation'])
        self.assertEqual(dataset.class_summary_json['image_count'], 1)

    def test_augmented_dataset_build_screen_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get('/datasets/build/augmented/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Augmented Dataset Build')
        self.assertContains(response, 'Target images per class')
        self.assertContains(response, 'Max augmentations per source image')
        self.assertContains(response, 'Color-safe augmentation')
        self.assertNotContains(response, 'Use augmentation')
        self.assertContains(response, 'Expected total')

    def test_augmented_dataset_build_post_starts_background_build(self):
        self.client.force_login(self.user)
        with patch('datasets.views.start_augmented_dataset_build') as mocked_start:
            response = self.client.post('/datasets/build/augmented/', {
                'name': 'dataset_augmented_post',
                'description': 'augmented dataset',
                'train_ratio': 80,
                'val_ratio': 10,
                'test_ratio': 10,
                'random_seed': 42,
                'include_only_labeled_images': 'on',
                'exclude_invalid_boxes': 'on',
                'build_memo': 'memo',
                'target_images_per_class': 3,
                'max_augmentations_per_source_image': 3,
                'color_safe_augmentation': 'on',
            })

        self.assertEqual(response.status_code, 302)
        dataset = DatasetVersion.objects.get(name='dataset_augmented_post')
        self.assertEqual(dataset.build_config_json['build_type'], 'augmented')
        self.assertTrue(dataset.build_config_json['use_augmentation'])
        self.assertTrue(dataset.build_config_json['background_build'])
        self.assertEqual(dataset.status, DatasetVersion.Status.PENDING)
        mocked_start.assert_called_once_with(dataset)

    def test_augmented_dataset_build_calls_augmentation_logic(self):
        form = AugmentedDatasetBuildForm(data={
            'name': 'dataset_augmented_call',
            'description': 'augmented dataset',
            'train_ratio': 80,
            'val_ratio': 10,
            'test_ratio': 10,
            'random_seed': 42,
            'include_only_labeled_images': 'on',
            'exclude_invalid_boxes': 'on',
            'target_images_per_class': 2,
            'max_augmentations_per_source_image': 2,
            'color_safe_augmentation': 'on',
        })
        self.assertTrue(form.is_valid(), form.errors)

        with patch('datasets.yolo_builder.augment_image_and_boxes') as mocked:
            with Image.open(self.image.file.path) as source:
                mocked.return_value = (source.convert('RGB').copy(), [{
                    'object_class_id': self.object_class.id,
                    'x_min': 3,
                    'y_min': 2,
                    'x_max': 9,
                    'y_max': 6,
                    'image_width': 12,
                    'image_height': 8,
                }])
            build_dataset_version(form, user=self.user, use_augmentation=True)

        self.assertTrue(mocked.called)

    def test_dataset_versions_screen_shows_type(self):
        DatasetVersion.objects.create(
            name='version_original',
            train_ratio=80,
            val_ratio=10,
            test_ratio=10,
            random_seed=42,
            build_config_json={'build_type': 'original'},
            class_summary_json={'image_count': 25},
            output_path='/tmp/version_original',
            status=DatasetVersion.Status.BUILT,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get('/datasets/versions/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Type')
        self.assertContains(response, 'Images')
        self.assertContains(response, 'original')
