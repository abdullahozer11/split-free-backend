STATICFILES_DIRS = [
    BASE_DIR / "static",  # type: ignore # noqa: F821
]

if USE_S3:  # type: ignore # noqa: F821
    AWS_STORAGE_BUCKET_NAME = "sfree-backend"
    AWS_S3_SIGNATURE_NAME = ("s3v4",)
    AWS_S3_REGION_NAME = "eu-west-3"
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_S3_VERIFY = True
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    # Set the S3 bucket URL for media files
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
else:
    MEDIA_URL = "/media/"
    STATIC_URL = "/static/"
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

STATIC_ROOT = BASE_DIR / "staticfiles"  # type: ignore # noqa: F821
MEDIA_ROOT = BASE_DIR / "media"  # type: ignore # noqa: F821
