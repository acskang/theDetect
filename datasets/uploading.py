import posixpath
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import PurePosixPath

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

from .models import ObjectClass, UploadedImage

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_ZIP_EXTENSIONS = {'.zip'}


@dataclass
class UploadSummary:
    created: int = 0
    skipped: int = 0
    invalid: int = 0
    errors: list[str] = field(default_factory=list)


def extension_for(filename):
    return PurePosixPath(filename).suffix.lower()


def resize_image_bytes(content, filename):
    if extension_for(filename) not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError('Unsupported image extension.')
    if len(content) > settings.MDETECT_MAX_UPLOAD_SIZE:
        raise ValueError('File exceeds upload size limit.')
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
        with Image.open(BytesIO(content)) as image:
            image = ImageOps.exif_transpose(image)
            max_long_edge = getattr(settings, 'MDETECT_MAX_IMAGE_LONG_EDGE', 1280)
            if max_long_edge and max(image.size) > max_long_edge:
                image.thumbnail((max_long_edge, max_long_edge), Image.Resampling.LANCZOS)
            if image.mode in {'RGBA', 'LA'} or (image.mode == 'P' and 'transparency' in image.info):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image.convert('RGBA'), mask=image.convert('RGBA').getchannel('A'))
                image = background
            else:
                image = image.convert('RGB')
            output = BytesIO()
            image.save(output, format='JPEG', quality=88, optimize=True)
            resized_content = output.getvalue()
            if len(resized_content) > settings.MDETECT_MAX_UPLOAD_SIZE:
                raise ValueError('Processed image exceeds upload size limit.')
            return resized_content, image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError('Invalid image file.') from exc


def create_uploaded_image(content, filename, upload_source, uploaded_by=None, hint_class=None):
    processed_content, (width, height) = resize_image_bytes(content, filename)
    stored_filename = f'{PurePosixPath(filename).stem}.jpg'
    record = UploadedImage.objects.create(
        file=ContentFile(processed_content, name=stored_filename),
        original_filename=filename[:255],
        width=width,
        height=height,
        file_size=len(processed_content),
        upload_source=upload_source,
        hint_class=hint_class,
        uploaded_by=uploaded_by if getattr(uploaded_by, 'is_authenticated', False) else None,
    )
    return record


def handle_multi_upload(files, uploaded_by=None, hint_class=None):
    summary = UploadSummary()
    for uploaded_file in files:
        try:
            content = uploaded_file.read()
            create_uploaded_image(
                content,
                uploaded_file.name,
                UploadedImage.UploadSource.MULTI,
                uploaded_by=uploaded_by,
                hint_class=hint_class,
            )
            summary.created += 1
        except ValueError as exc:
            summary.invalid += 1
            summary.errors.append(f'{uploaded_file.name}: {exc}')
        except Exception as exc:
            summary.skipped += 1
            summary.errors.append(f'{uploaded_file.name}: upload failed ({exc})')
    return summary


def safe_zip_member_name(member_name):
    if not member_name or member_name.endswith('/'):
        return None
    normalized = posixpath.normpath(member_name.replace('\\', '/'))
    path = PurePosixPath(normalized)
    if path.is_absolute() or normalized.startswith('../') or '..' in path.parts or any(':' in part for part in path.parts):
        return None
    if extension_for(path.name) not in ALLOWED_IMAGE_EXTENSIONS:
        return None
    return path


def hint_class_for_zip_path(path):
    if len(path.parts) < 2:
        return None
    return ObjectClass.objects.filter(name=path.parts[0]).first()


def handle_zip_upload(zip_file, uploaded_by=None, hint_class=None):
    summary = UploadSummary()
    if extension_for(zip_file.name) not in ALLOWED_ZIP_EXTENSIONS:
        summary.invalid += 1
        summary.errors.append(f'{zip_file.name}: unsupported ZIP extension.')
        return summary
    try:
        with zipfile.ZipFile(zip_file) as archive:
            for member in archive.infolist():
                member_path = safe_zip_member_name(member.filename)
                if member_path is None:
                    summary.skipped += 1
                    continue
                if member.file_size > settings.MDETECT_MAX_UPLOAD_SIZE:
                    summary.invalid += 1
                    summary.errors.append(f'{member.filename}: file exceeds upload size limit.')
                    continue
                try:
                    content = archive.read(member)
                    create_uploaded_image(
                        content,
                        member_path.name,
                        UploadedImage.UploadSource.ZIP,
                        uploaded_by=uploaded_by,
                        hint_class=hint_class or hint_class_for_zip_path(member_path),
                    )
                    summary.created += 1
                except ValueError as exc:
                    summary.invalid += 1
                    summary.errors.append(f'{member.filename}: {exc}')
    except zipfile.BadZipFile:
        summary.invalid += 1
        summary.errors.append(f'{zip_file.name}: invalid ZIP file.')
    return summary
