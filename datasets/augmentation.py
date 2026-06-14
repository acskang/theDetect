import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


@dataclass(frozen=True)
class AugmentationPolicy:
    color_safe: bool = True
    brightness_min: float = 0.85
    brightness_max: float = 1.15
    contrast_min: float = 0.85
    contrast_max: float = 1.15
    scale_min: float = 0.9
    scale_max: float = 1.1
    shift_ratio: float = 0.05
    blur_probability: float = 0.12
    noise_probability: float = 0.12
    blur_radius: float = 0.65
    noise_delta: int = 7
    min_box_area_ratio: float = 0.0005


def color_safe_policy():
    return AugmentationPolicy(color_safe=True)


def implemented_augmentation_names():
    return ['brightness', 'contrast', 'blur', 'noise', 'horizontal_shift', 'vertical_shift', 'scale']


def deferred_augmentation_names():
    return ['rotation', 'perspective', 'hue_shift', 'saturation_shift']


def clip_box(box, width, height, min_area_ratio):
    x_min, y_min, x_max, y_max = box
    x_min = max(0, min(round(x_min), width))
    y_min = max(0, min(round(y_min), height))
    x_max = max(0, min(round(x_max), width))
    y_max = max(0, min(round(y_max), height))
    if x_min >= x_max or y_min >= y_max:
        return None
    area = (x_max - x_min) * (y_max - y_min)
    if area / (width * height) < min_area_ratio:
        return None
    return x_min, y_min, x_max, y_max


def transform_boxes_for_affine(boxes, width, height, scale, shift_x, shift_y, min_area_ratio):
    transformed = []
    scaled_width = width * scale
    scaled_height = height * scale
    offset_x = (width - scaled_width) / 2 + shift_x
    offset_y = (height - scaled_height) / 2 + shift_y
    for box in boxes:
        new_box = (
            box['x_min'] * scale + offset_x,
            box['y_min'] * scale + offset_y,
            box['x_max'] * scale + offset_x,
            box['y_max'] * scale + offset_y,
        )
        clipped = clip_box(new_box, width, height, min_area_ratio)
        if clipped is None:
            continue
        transformed.append({**box, 'x_min': clipped[0], 'y_min': clipped[1], 'x_max': clipped[2], 'y_max': clipped[3]})
    return transformed


def add_noise(image, rng, delta):
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            noise = rng.randint(-delta, delta)
            pixels[x, y] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise)),
            )
    return image


def augment_image_and_boxes(source_path, boxes, seed, policy=None):
    policy = policy or color_safe_policy()
    rng = random.Random(seed)
    with Image.open(source_path) as original:
        image = original.convert('RGB')

    width, height = image.size
    scale = rng.uniform(policy.scale_min, policy.scale_max)
    shift_x = rng.uniform(-policy.shift_ratio, policy.shift_ratio) * width
    shift_y = rng.uniform(-policy.shift_ratio, policy.shift_ratio) * height
    scaled_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    scaled = image.resize(scaled_size, Image.Resampling.BICUBIC)
    canvas = Image.new('RGB', (width, height), (0, 0, 0))
    paste_x = round((width - scaled_size[0]) / 2 + shift_x)
    paste_y = round((height - scaled_size[1]) / 2 + shift_y)
    canvas.paste(scaled, (paste_x, paste_y))
    image = canvas

    image = ImageEnhance.Brightness(image).enhance(rng.uniform(policy.brightness_min, policy.brightness_max))
    image = ImageEnhance.Contrast(image).enhance(rng.uniform(policy.contrast_min, policy.contrast_max))
    if rng.random() < policy.blur_probability:
        image = image.filter(ImageFilter.GaussianBlur(radius=policy.blur_radius))
    if rng.random() < policy.noise_probability:
        image = add_noise(image, rng, policy.noise_delta)

    transformed_boxes = transform_boxes_for_affine(
        boxes,
        width,
        height,
        scale,
        shift_x,
        shift_y,
        policy.min_box_area_ratio,
    )
    return image, transformed_boxes


def save_augmented_jpeg(image, path):
    path = Path(path)
    image.save(path, format='JPEG', quality=88, optimize=True)
