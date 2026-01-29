# Django Storage

## Supported backends
- MinIO
- Backblaze B2

## Installation
```bash
pip install django-storage
```

## Usage

### BackBlazeB2
*Reads configuration from Django settings when not provided explicitly:*

```python
# For Django 4.2+

STORAGE_B2_APP_KEY = ""
STORAGE_B2_ACCOUNT_ID = ""
STORAGE_B2_BUCKET_NAME = ""
STORAGE_B2_BUCKET_ID = ""

STORAGES = {
    "default": {
        "BACKEND": "django_object_storage.b2.B2Storage",
    },
}

# Or for Django 4.2+ with options
STORAGES = {
    "default": {
        "BACKEND": "django_object_storage.b2.B2Storage",
        "OPTIONS": {
            "account_id": "",
            "app_key": "",
            "bucket_name": "",
            "bucket_id": "",
        },
    },
}

# For Django versions below 4.2
DEFAULT_FILE_STORAGE = "django_object_storage.b2.B2Storage"
```

### MinIO

Reads configuration from Django settings when not provided explicitly:

```python
# For Django 4.2+

STORAGE_MINIO_BUCKET_NAME = ""
STORAGE_MINIO_ENDPOINT = "" # s3.example.com
STORAGE_MINIO_ACCESS_KEY = ""
STORAGE_MINIO_SECRET_KEY = ""
STORAGE_MINIO_SECURE = True  # True or False

STORAGES = {
    "default": {
        "BACKEND": "django_object_storage.minio.MinIOStorage",
    },
}

# Or for Django 4.2+ with options
STORAGES = {
    "default": {
        "BACKEND": "django_object_storage.minio.MinIOStorage",
        "OPTIONS": {
            "bucket_name": "",
            "endpoint": "", # s3.example.com
            "access_key": "",
            "secret_key": "",
            "secure": True,  # True or False
        },
    },
}

# For Django versions below 4.2
DEFAULT_FILE_STORAGE = "django_object_storage.minio.MinIOStorage"
```