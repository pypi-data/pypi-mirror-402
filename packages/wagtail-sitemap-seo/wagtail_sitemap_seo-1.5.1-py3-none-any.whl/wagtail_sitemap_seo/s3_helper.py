from django.core.files.base import ContentFile

from .storage import SitemapS3Storage


def save_xml(name: str, content: bytes) -> str:
    """
    Save an XML file using Django's default storage.

    - In dev (SITEMAP_WRITE_S3): saves to MEDIA_ROOT
    - In ECS/UAT (SITEMAP_WRITE_S3=True): saves to S3 bucket root (because your default storage is S3Boto3Storage)

    Returns the final storage path.
    """
    storage = SitemapS3Storage()
    if storage.exists(name):
        storage.delete(name)
    return storage.save(name, ContentFile(content))