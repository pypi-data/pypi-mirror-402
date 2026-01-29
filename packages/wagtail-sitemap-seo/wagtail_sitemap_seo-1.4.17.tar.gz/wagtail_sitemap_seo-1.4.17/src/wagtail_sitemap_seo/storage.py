from storages.backends.s3boto3 import S3Boto3Storage


class SitemapS3Storage(S3Boto3Storage):
    """
    S3 storage for sitemaps that overwrites existing keys.
    Keeps the project's global AWS_S3_FILE_OVERWRITE=False untouched.
    """
    file_overwrite = True
