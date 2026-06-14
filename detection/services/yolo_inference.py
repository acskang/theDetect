from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from django.conf import settings
from PIL import Image, UnidentifiedImageError


ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
DEFAULT_CONFIDENCE = 0.15
DEFAULT_IOU = 0.45
DEFAULT_IMAGE_SIZE = 640

_MODEL_CACHE = {
    'key': None,
    'model': None,
}


class ImageValidationError(ValueError):
    pass


class InferenceError(RuntimeError):
    pass


@dataclass
class ValidatedImage:
    image: Image.Image
    width: int
    height: int


@dataclass
class InferenceResult:
    detections: list
    image_width: int
    image_height: int
    model_version: str


def validate_uploaded_image(uploaded_file):
    if uploaded_file is None:
        raise ImageValidationError('image is required.')

    filename = getattr(uploaded_file, 'name', '') or ''
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ImageValidationError('Unsupported image type. Use jpg, jpeg, png, or webp.')

    max_size = getattr(settings, 'MDETECT_MAX_UPLOAD_SIZE', 20 * 1024 * 1024)
    file_size = getattr(uploaded_file, 'size', 0) or 0
    if file_size <= 0:
        raise ImageValidationError('Uploaded image is empty.')
    if file_size > max_size:
        raise ImageValidationError(f'Uploaded image is too large. Max size is {max_size} bytes.')

    content = uploaded_file.read()
    uploaded_file.seek(0)
    if not content:
        raise ImageValidationError('Uploaded image is empty.')

    try:
        with Image.open(BytesIO(content)) as probe:
            probe.verify()
        with Image.open(BytesIO(content)) as source:
            image = source.convert('RGB')
            width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError('Uploaded file is not a valid image.') from exc

    if width <= 0 or height <= 0:
        raise ImageValidationError('Uploaded image has invalid dimensions.')
    return ValidatedImage(image=image, width=width, height=height)


def active_model_cache_key(trained_model):
    model_path = Path(trained_model.model_path) if trained_model.model_path else None
    if not model_path:
        raise InferenceError('Active server model does not have a model_path.')
    if not model_path.exists() or not model_path.is_file():
        raise InferenceError(f'Active server model file does not exist: {model_path}')
    return (trained_model.id, str(model_path.resolve()), model_path.stat().st_mtime_ns)


def get_cached_yolo_model(trained_model):
    cache_key = active_model_cache_key(trained_model)
    if _MODEL_CACHE['key'] == cache_key and _MODEL_CACHE['model'] is not None:
        return _MODEL_CACHE['model']

    try:
        from ultralytics import YOLO
    except Exception as exc:
        raise InferenceError('Ultralytics YOLO is not available in this environment.') from exc

    try:
        model = YOLO(cache_key[1])
    except Exception as exc:
        raise InferenceError(f'Failed to load active server model: {exc}') from exc

    _MODEL_CACHE['key'] = cache_key
    _MODEL_CACHE['model'] = model
    return model


def clear_model_cache():
    _MODEL_CACHE['key'] = None
    _MODEL_CACHE['model'] = None


def run_yolo_inference(trained_model, validated_image, conf=DEFAULT_CONFIDENCE, iou=DEFAULT_IOU, imgsz=None):
    model = get_cached_yolo_model(trained_model)
    image_size = imgsz or getattr(getattr(trained_model, 'training_job', None), 'imgsz', None) or DEFAULT_IMAGE_SIZE

    try:
        results = model(
            validated_image.image,
            conf=conf,
            iou=iou,
            imgsz=image_size,
            verbose=False,
        )
    except Exception as exc:
        raise InferenceError(f'YOLO inference failed: {exc}') from exc

    detections = convert_yolo_results(
        results=results,
        image_width=validated_image.width,
        image_height=validated_image.height,
        trained_model=trained_model,
        yolo_model=model,
    )
    return InferenceResult(
        detections=detections,
        image_width=validated_image.width,
        image_height=validated_image.height,
        model_version=trained_model.name,
    )


def convert_yolo_results(results, image_width, image_height, trained_model=None, yolo_model=None):
    if not results:
        return []

    first_result = results[0]
    boxes = getattr(first_result, 'boxes', None)
    if boxes is None:
        return []

    xyxy_values = to_plain_list(getattr(boxes, 'xyxy', []))
    confidence_values = to_plain_list(getattr(boxes, 'conf', []))
    class_values = to_plain_list(getattr(boxes, 'cls', []))
    names = class_name_mapping(trained_model, yolo_model)

    detections = []
    for coords, confidence, class_id in zip(xyxy_values, confidence_values, class_values):
        if len(coords) < 4:
            continue
        class_id = int(class_id)
        x_min, y_min, x_max, y_max = clamp_box(coords, image_width, image_height)
        if x_min >= x_max or y_min >= y_max:
            continue
        detections.append({
            'class_id': class_id,
            'class_name': names.get(class_id, f'class_{class_id}'),
            'confidence': round(float(confidence), 6),
            'box': {
                'x_min': x_min,
                'y_min': y_min,
                'x_max': x_max,
                'y_max': y_max,
            },
        })
    return detections


def to_plain_list(value):
    if value is None:
        return []
    if hasattr(value, 'detach'):
        value = value.detach()
    if hasattr(value, 'cpu'):
        value = value.cpu()
    if hasattr(value, 'numpy'):
        value = value.numpy()
    if hasattr(value, 'tolist'):
        return value.tolist()
    return list(value)


def clamp_box(coords, image_width, image_height):
    x_min, y_min, x_max, y_max = [float(item) for item in coords[:4]]
    x_min = max(0, min(round(x_min), image_width))
    y_min = max(0, min(round(y_min), image_height))
    x_max = max(0, min(round(x_max), image_width))
    y_max = max(0, min(round(y_max), image_height))
    return x_min, y_min, x_max, y_max


def class_name_mapping(trained_model=None, yolo_model=None):
    for raw_names in (
        getattr(trained_model, 'class_names_json', None),
        getattr(yolo_model, 'names', None),
    ):
        names = normalize_class_names(raw_names)
        if names:
            return names
    return {}


def normalize_class_names(raw_names):
    if isinstance(raw_names, list):
        return {index: str(name) for index, name in enumerate(raw_names)}
    if isinstance(raw_names, dict):
        names = {}
        for key, value in raw_names.items():
            try:
                class_id = int(key)
            except (TypeError, ValueError):
                continue
            if isinstance(value, dict):
                value = value.get('name') or value.get('display_name') or value
            names[class_id] = str(value)
        return names
    return {}
