import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils.text import slugify

from labeling.models import LabelBox

from .augmentation import (
    augment_image_and_boxes,
    color_safe_policy,
    deferred_augmentation_names,
    implemented_augmentation_names,
    save_augmented_jpeg,
)
from .models import DatasetVersion, ObjectClass, UploadedImage


def yolo_box_coordinates(box):
    x_center = ((box.x_min + box.x_max) / 2) / box.image_width
    y_center = ((box.y_min + box.y_max) / 2) / box.image_height
    width = (box.x_max - box.x_min) / box.image_width
    height = (box.y_max - box.y_min) / box.image_height
    values = (x_center, y_center, width, height)
    if any(value < 0 or value > 1 for value in values):
        raise ValueError('YOLO coordinates must be normalized between 0 and 1.')
    return values


def class_mapping():
    classes = list(ObjectClass.objects.filter(is_active=True).order_by('sort_order', 'id', 'name'))
    return {
        obj.id: {'id': index, 'name': obj.name, 'display_name': obj.display_name}
        for index, obj in enumerate(classes)
    }


def split_images(images, train_ratio, val_ratio, test_ratio, seed):
    shuffled = list(images)
    random.Random(seed).shuffle(shuffled)
    total = len(shuffled)
    if total == 0:
        return {'train': [], 'val': [], 'test': []}
    train_count = round(total * train_ratio / 100)
    val_count = round(total * val_ratio / 100)
    if train_count == 0:
        train_count = 1
    if total >= 3 and val_count == 0:
        val_count = 1
    if train_count + val_count >= total:
        val_count = max(0, total - train_count - 1)
    _ = test_ratio
    return {
        'train': shuffled[:train_count],
        'val': shuffled[train_count:train_count + val_count],
        'test': shuffled[train_count + val_count:],
    }


def valid_box(box):
    return (
        box.x_min >= 0
        and box.y_min >= 0
        and box.x_min < box.x_max <= box.image_width
        and box.y_min < box.y_max <= box.image_height
    )


def dataset_warnings(include_only_labeled_images=True, augmentation_options=None):
    mapping = class_mapping()
    label_counts = Counter(LabelBox.objects.filter(object_class_id__in=mapping.keys()).values_list('object_class_id', flat=True))
    warnings = []
    for object_class_id, info in mapping.items():
        count = label_counts.get(object_class_id, 0)
        if count == 0:
            warnings.append(f'{info["name"]} has no labels.')
        elif count < 3:
            warnings.append(f'{info["name"]} has only {count} label(s).')
    other = ObjectClass.objects.filter(name='other').first()
    if other and label_counts.get(other.id, 0):
        non_other_counts = [count for class_id, count in label_counts.items() if class_id != other.id]
        if non_other_counts and label_counts[other.id] > sum(non_other_counts):
            warnings.append('other labels exceed all target-class labels combined.')
    invalid_count = sum(1 for box in LabelBox.objects.select_related('image') if not valid_box(box))
    if invalid_count:
        warnings.append(f'{invalid_count} invalid box(es) found.')
    unlabeled_count = UploadedImage.objects.filter(label_boxes__isnull=True).count()
    if unlabeled_count >= 5:
        warnings.append(f'{unlabeled_count} uploaded image(s) have no labels.')
    if include_only_labeled_images:
        candidates = UploadedImage.objects.filter(status=UploadedImage.Status.LABELED, label_boxes__isnull=False).distinct().count()
        if candidates == 0:
            warnings.append('No labeled images are ready for dataset build.')
    if augmentation_options and augmentation_options.get('use_augmentation'):
        target = augmentation_options.get('target_images_per_class') or 500
        image_counts = source_image_counts_by_class(include_only_labeled_images=include_only_labeled_images)
        for object_class_id, info in mapping.items():
            source_count = image_counts.get(object_class_id, 0)
            if source_count and source_count < 10:
                warnings.append(f'{info["name"]} has only {source_count} source image(s); augmentation may overfit.')
            if source_count and target / source_count >= 50:
                warnings.append(f'{info["name"]} target count is at least 50x source images.')
        other = ObjectClass.objects.filter(name='other').first()
        if other and image_counts.get(other.id, 0) < 10:
            warnings.append('other class has fewer than 10 source images.')
        for name in ('soap_case_white', 'soap_case_mint', 'shampoo_case_white'):
            object_class = ObjectClass.objects.filter(name=name).first() or ObjectClass.objects.filter(display_name=name).first()
            if object_class and image_counts.get(object_class.id, 0) < 10:
                warnings.append(f'{name} has fewer than 10 source images; color/product confusion risk remains high.')
    return warnings


def source_image_counts_by_class(include_only_labeled_images=True):
    queryset = LabelBox.objects.select_related('image')
    if include_only_labeled_images:
        queryset = queryset.filter(image__status=UploadedImage.Status.LABELED)
    counts = defaultdict(set)
    for object_class_id, image_id in queryset.values_list('object_class_id', 'image_id'):
        counts[object_class_id].add(image_id)
    return {object_class_id: len(image_ids) for object_class_id, image_ids in counts.items()}


def write_data_yaml(output_dir, mapping):
    names = sorted(mapping.values(), key=lambda item: item['id'])
    lines = [
        f'path: {output_dir}',
        'train: images/train',
        'val: images/val',
        'test: images/test',
        'names:',
    ]
    for item in names:
        lines.append(f'  {item["id"]}: {item["name"]}')
    data_yaml = output_dir / 'data.yaml'
    data_yaml.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return data_yaml


def box_to_dict(box):
    return {
        'object_class_id': box.object_class_id,
        'x_min': box.x_min,
        'y_min': box.y_min,
        'x_max': box.x_max,
        'y_max': box.y_max,
        'image_width': box.image_width,
        'image_height': box.image_height,
    }


def yolo_coordinates_from_dict(box, width, height):
    x_center = ((box['x_min'] + box['x_max']) / 2) / width
    y_center = ((box['y_min'] + box['y_max']) / 2) / height
    box_width = (box['x_max'] - box['x_min']) / width
    box_height = (box['y_max'] - box['y_min']) / height
    values = (x_center, y_center, box_width, box_height)
    if any(value < 0 or value > 1 for value in values):
        raise ValueError('YOLO coordinates must be normalized between 0 and 1.')
    return values


def write_label_file(label_target, boxes, mapping, width, height, split_class_counts):
    lines = []
    for box in boxes:
        object_class_id = box['object_class_id']
        if object_class_id not in mapping:
            continue
        coords = yolo_coordinates_from_dict(box, width, height)
        class_id = mapping[object_class_id]['id']
        split_class_counts[mapping[object_class_id]['name']] += 1
        lines.append(f'{class_id} ' + ' '.join(f'{value:.6f}' for value in coords))
    label_target.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
    return len(lines)


def original_boxes_for_image(image, mapping, exclude_invalid):
    boxes = []
    for box in image.label_boxes.all():
        if box.object_class_id not in mapping:
            continue
        if not valid_box(box):
            if exclude_invalid:
                continue
            raise ValueError(f'Invalid box for image {image.id}.')
        boxes.append(box_to_dict(box))
    return boxes


def safe_augmented_stem(class_name, image, aug_index):
    source_stem = Path(image.file.name).stem
    return f'{class_name}_{source_stem}_aug{aug_index:04d}'


def prepare_augmented_dataset_version(form, user=None):
    cleaned = form.cleaned_data
    include_only_labeled = cleaned.get('include_only_labeled_images', True)
    exclude_invalid = cleaned.get('exclude_invalid_boxes', True)
    target_per_class = cleaned.get('target_images_per_class') or 500
    max_per_source = cleaned.get('max_augmentations_per_source_image') or 0
    color_safe = cleaned.get('color_safe_augmentation', True)
    mapping = class_mapping()
    queryset = UploadedImage.objects.prefetch_related('label_boxes__object_class').filter(label_boxes__isnull=False).distinct()
    if include_only_labeled:
        queryset = queryset.filter(status=UploadedImage.Status.LABELED)
    if not queryset.exists():
        raise ValueError('No labeled images are available for dataset build.')

    safe_name = slugify(cleaned['name']) or cleaned['name'].replace(' ', '_')
    output_dir = Path(settings.PROJECT_DATA_DIR) / 'datasets' / safe_name
    if output_dir.exists():
        raise ValueError(f'Dataset output already exists: {output_dir}')
    warnings = dataset_warnings(
        include_only_labeled,
        {
            'use_augmentation': True,
            'target_images_per_class': target_per_class,
        },
    )
    return DatasetVersion.objects.create(
        name=cleaned['name'],
        description=cleaned.get('description', ''),
        train_ratio=cleaned['train_ratio'],
        val_ratio=cleaned['val_ratio'],
        test_ratio=cleaned['test_ratio'],
        random_seed=cleaned['random_seed'],
        class_summary_json={'mapping': mapping, 'warnings': warnings},
        build_config_json={
            'build_type': 'augmented',
            'include_only_labeled_images': include_only_labeled,
            'exclude_invalid_boxes': exclude_invalid,
            'build_memo': cleaned.get('build_memo', ''),
            'use_augmentation': True,
            'target_images_per_class': target_per_class,
            'max_augmentations_per_source_image': max_per_source,
            'color_safe_augmentation': color_safe,
            'augmentation_methods': implemented_augmentation_names(),
            'implemented_augmentations': implemented_augmentation_names(),
            'deferred_augmentations': deferred_augmentation_names(),
            'train_ratio': cleaned['train_ratio'],
            'val_ratio': cleaned['val_ratio'],
            'test_ratio': cleaned['test_ratio'],
            'random_seed': cleaned['random_seed'],
            'background_build': True,
        },
        output_path=str(output_dir),
        status=DatasetVersion.Status.PENDING,
        created_by=user if getattr(user, 'is_authenticated', False) else None,
    )


def build_augmented_dataset_version(form, user=None, dataset=None):
    cleaned = form.cleaned_data
    include_only_labeled = cleaned.get('include_only_labeled_images', True)
    exclude_invalid = cleaned.get('exclude_invalid_boxes', True)
    target_per_class = cleaned.get('target_images_per_class') or 500
    max_per_source = cleaned.get('max_augmentations_per_source_image') or 0
    color_safe = cleaned.get('color_safe_augmentation', True)
    mapping = class_mapping()
    queryset = UploadedImage.objects.prefetch_related('label_boxes__object_class').filter(label_boxes__isnull=False).distinct()
    if include_only_labeled:
        queryset = queryset.filter(status=UploadedImage.Status.LABELED)
    images = list(queryset)
    if not images:
        raise ValueError('No labeled images are available for dataset build.')

    splits = split_images(
        images,
        cleaned['train_ratio'],
        cleaned['val_ratio'],
        cleaned['test_ratio'],
        cleaned['random_seed'],
    )
    safe_name = slugify(cleaned['name']) or cleaned['name'].replace(' ', '_')
    output_dir = Path(dataset.output_path) if dataset is not None else Path(settings.PROJECT_DATA_DIR) / 'datasets' / safe_name
    if output_dir.exists():
        raise ValueError(f'Dataset output already exists: {output_dir}')
    for split in ('train', 'val', 'test'):
        (output_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)

    split_by_image_id = {
        image.id: split
        for split, split_images_for_build in splits.items()
        for image in split_images_for_build
    }
    image_boxes = {image.id: original_boxes_for_image(image, mapping, exclude_invalid) for image in images}
    class_to_images = defaultdict(list)
    for image in images:
        class_ids = {box['object_class_id'] for box in image_boxes[image.id]}
        for object_class_id in class_ids:
            class_to_images[object_class_id].append(image)

    split_class_counts = defaultdict(Counter)
    image_count = 0
    generated_count = 0
    skipped_augmented = 0
    per_source_generated = Counter()
    warnings = dataset_warnings(
        include_only_labeled,
        {
            'use_augmentation': True,
            'target_images_per_class': target_per_class,
        },
    )
    policy = color_safe_policy()
    rng = random.Random(cleaned['random_seed'])

    with transaction.atomic():
        if dataset is None:
            dataset = DatasetVersion.objects.create(
                name=cleaned['name'],
                description=cleaned.get('description', ''),
                train_ratio=cleaned['train_ratio'],
                val_ratio=cleaned['val_ratio'],
                test_ratio=cleaned['test_ratio'],
                random_seed=cleaned['random_seed'],
                class_summary_json={'mapping': mapping, 'warnings': warnings},
                build_config_json={
                    'build_type': 'augmented',
                    'include_only_labeled_images': include_only_labeled,
                    'exclude_invalid_boxes': exclude_invalid,
                    'build_memo': cleaned.get('build_memo', ''),
                    'use_augmentation': True,
                    'target_images_per_class': target_per_class,
                    'max_augmentations_per_source_image': max_per_source,
                    'color_safe_augmentation': color_safe,
                    'augmentation_methods': implemented_augmentation_names(),
                    'implemented_augmentations': implemented_augmentation_names(),
                    'deferred_augmentations': deferred_augmentation_names(),
                    'train_ratio': cleaned['train_ratio'],
                    'val_ratio': cleaned['val_ratio'],
                    'test_ratio': cleaned['test_ratio'],
                    'random_seed': cleaned['random_seed'],
                    'splits': {name: [image.id for image in images_for_split] for name, images_for_split in splits.items()},
                },
                output_path=str(output_dir),
                status=DatasetVersion.Status.PENDING,
                created_by=user if getattr(user, 'is_authenticated', False) else None,
            )
        else:
            dataset.build_config_json = {
                **dataset.build_config_json,
                'splits': {name: [image.id for image in images_for_split] for name, images_for_split in splits.items()},
            }
            dataset.save(update_fields=['build_config_json'])

        try:
            for split, split_images_for_build in splits.items():
                for image in split_images_for_build:
                    source_path = Path(image.file.path)
                    image_target = output_dir / 'images' / split / source_path.name
                    label_target = output_dir / 'labels' / split / f'{source_path.stem}.txt'
                    shutil.copy2(source_path, image_target)
                    write_label_file(label_target, image_boxes[image.id], mapping, image.width, image.height, split_class_counts[split])
                    image_count += 1

            for object_class_id, info in mapping.items():
                source_images = class_to_images.get(object_class_id, [])
                if not source_images:
                    continue
                current_count = len(source_images)
                attempts = 0
                aug_index = 1
                max_attempts = max(target_per_class * 10, len(source_images) * max(max_per_source, 1) * 2)
                while current_count < target_per_class and attempts < max_attempts:
                    attempts += 1
                    candidates = [image for image in source_images if per_source_generated[(object_class_id, image.id)] < max_per_source]
                    if not candidates:
                        warnings.append(f'{info["name"]} could not reach target count because max augmentations per source image was reached.')
                        break
                    image = rng.choice(candidates)
                    split = split_by_image_id[image.id]
                    seed = rng.randint(1, 2_147_483_647)
                    augmented_image, augmented_boxes = augment_image_and_boxes(
                        image.file.path,
                        image_boxes[image.id],
                        seed=seed,
                        policy=policy,
                    )
                    if not any(box['object_class_id'] == object_class_id for box in augmented_boxes):
                        skipped_augmented += 1
                        continue
                    stem = safe_augmented_stem(info['name'], image, aug_index)
                    aug_index += 1
                    image_target = output_dir / 'images' / split / f'{stem}.jpg'
                    label_target = output_dir / 'labels' / split / f'{stem}.txt'
                    save_augmented_jpeg(augmented_image, image_target)
                    written = write_label_file(label_target, augmented_boxes, mapping, image.width, image.height, split_class_counts[split])
                    if written == 0:
                        image_target.unlink(missing_ok=True)
                        label_target.unlink(missing_ok=True)
                        skipped_augmented += 1
                        continue
                    per_source_generated[(object_class_id, image.id)] += 1
                    current_count += 1
                    generated_count += 1
                    image_count += 1

            data_yaml = write_data_yaml(output_dir, mapping)
            class_names = [item['name'] for item in sorted(mapping.values(), key=lambda item: item['id'])]
            for split in ('train', 'val', 'test'):
                if splits[split]:
                    missing = [name for name in class_names if split_class_counts[split].get(name, 0) == 0]
                    if missing:
                        warnings.append(f'{split} split is missing labels for: {", ".join(missing)}.')
            dataset.class_summary_json = {
                'mapping': mapping,
                'class_names': class_names,
                'split_class_counts': {split: dict(counts) for split, counts in split_class_counts.items()},
                'warnings': warnings,
                'image_count': image_count,
                'original_image_count': len(images),
                'augmented_image_count': generated_count,
                'skipped_augmented_count': skipped_augmented,
                'source_image_splits': {image_id: split for image_id, split in split_by_image_id.items()},
                'data_yaml': str(data_yaml),
            }
            dataset.status = DatasetVersion.Status.BUILT
            dataset.save(update_fields=['class_summary_json', 'status'])
        except Exception:
            dataset.status = DatasetVersion.Status.FAILED
            dataset.save(update_fields=['status'])
            raise
    return dataset


def build_dataset_version(form, user=None, use_augmentation=None):
    cleaned = form.cleaned_data
    if use_augmentation is None:
        use_augmentation = cleaned.get('use_augmentation', False)
    if use_augmentation:
        return build_augmented_dataset_version(form, user=user)
    include_only_labeled = form.cleaned_data.get('include_only_labeled_images', True)
    exclude_invalid = form.cleaned_data.get('exclude_invalid_boxes', True)
    mapping = class_mapping()
    queryset = UploadedImage.objects.prefetch_related('label_boxes__object_class').filter(label_boxes__isnull=False).distinct()
    if include_only_labeled:
        queryset = queryset.filter(status=UploadedImage.Status.LABELED)
    images = list(queryset)
    if not images:
        raise ValueError('No labeled images are available for dataset build.')

    splits = split_images(
        images,
        cleaned['train_ratio'],
        cleaned['val_ratio'],
        cleaned['test_ratio'],
        cleaned['random_seed'],
    )
    safe_name = slugify(cleaned['name']) or cleaned['name'].replace(' ', '_')
    output_dir = Path(settings.PROJECT_DATA_DIR) / 'datasets' / safe_name
    if output_dir.exists():
        raise ValueError(f'Dataset output already exists: {output_dir}')
    for split in ('train', 'val', 'test'):
        (output_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)

    split_class_counts = defaultdict(Counter)
    image_count = 0
    with transaction.atomic():
        dataset = DatasetVersion.objects.create(
            name=cleaned['name'],
            description=cleaned.get('description', ''),
            train_ratio=cleaned['train_ratio'],
            val_ratio=cleaned['val_ratio'],
            test_ratio=cleaned['test_ratio'],
            random_seed=cleaned['random_seed'],
            class_summary_json={'mapping': mapping, 'warnings': dataset_warnings(include_only_labeled)},
            build_config_json={
                'build_type': 'original',
                'include_only_labeled_images': include_only_labeled,
                'exclude_invalid_boxes': exclude_invalid,
                'build_memo': form.cleaned_data.get('build_memo', ''),
                'use_augmentation': False,
                'train_ratio': cleaned['train_ratio'],
                'val_ratio': cleaned['val_ratio'],
                'test_ratio': cleaned['test_ratio'],
                'random_seed': cleaned['random_seed'],
                'splits': {name: [image.id for image in images_for_split] for name, images_for_split in splits.items()},
            },
            output_path=str(output_dir),
            status=DatasetVersion.Status.PENDING,
            created_by=user if getattr(user, 'is_authenticated', False) else None,
        )

        try:
            for split, split_images_for_build in splits.items():
                for image in split_images_for_build:
                    source_path = Path(image.file.path)
                    image_target = output_dir / 'images' / split / source_path.name
                    label_target = output_dir / 'labels' / split / f'{source_path.stem}.txt'
                    shutil.copy2(source_path, image_target)
                    lines = []
                    for box in image.label_boxes.all():
                        if box.object_class_id not in mapping:
                            continue
                        if not valid_box(box):
                            if exclude_invalid:
                                continue
                            raise ValueError(f'Invalid box for image {image.id}.')
                        coords = yolo_box_coordinates(box)
                        class_id = mapping[box.object_class_id]['id']
                        split_class_counts[split][mapping[box.object_class_id]['name']] += 1
                        lines.append(f'{class_id} ' + ' '.join(f'{value:.6f}' for value in coords))
                    label_target.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
                    image_count += 1
            data_yaml = write_data_yaml(output_dir, mapping)
            warnings = list(dataset.class_summary_json.get('warnings', []))
            class_names = [item['name'] for item in sorted(mapping.values(), key=lambda item: item['id'])]
            for split in ('train', 'val', 'test'):
                if splits[split]:
                    missing = [name for name in class_names if split_class_counts[split].get(name, 0) == 0]
                    if missing:
                        warnings.append(f'{split} split is missing labels for: {", ".join(missing)}.')
            dataset.class_summary_json = {
                'mapping': mapping,
                'class_names': class_names,
                'split_class_counts': {split: dict(counts) for split, counts in split_class_counts.items()},
                'warnings': warnings,
                'image_count': image_count,
                'data_yaml': str(data_yaml),
            }
            dataset.status = DatasetVersion.Status.BUILT
            dataset.save(update_fields=['class_summary_json', 'status'])
        except Exception:
            dataset.status = DatasetVersion.Status.FAILED
            dataset.save(update_fields=['status'])
            raise
    return dataset
