"""S3 storage backends for static files and media."""

from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """
    Storage backend for static files served via CDN.

    Configure with LIGHTWAVE_STATIC_PREFIX setting to set project-specific path.
    Example: LIGHTWAVE_STATIC_PREFIX = "static/api-lightwave-media-ltd"
    """

    default_acl = "public-read"
    file_overwrite = True

    def __init__(self, **kwargs):
        from django.conf import settings

        kwargs.setdefault("location", getattr(settings, "LIGHTWAVE_STATIC_PREFIX", "static"))
        super().__init__(**kwargs)


class PublicMediaStorage(S3Boto3Storage):
    """Storage backend for public media files (user uploads, etc)."""

    location = "media"
    default_acl = "public-read"
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    """Storage backend for private media files (protected downloads, etc)."""

    location = "private"
    default_acl = "private"
    file_overwrite = False
    custom_domain = False


def get_private_file_storage():
    """
    Get the appropriate private file storage backend.

    Returns PrivateMediaStorage if USE_S3_MEDIA is True, else FileSystemStorage.
    """
    from django.conf import settings

    if getattr(settings, "USE_S3_MEDIA", False):
        return PrivateMediaStorage()
    return FileSystemStorage()
