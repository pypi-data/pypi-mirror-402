from django.conf import settings
from django.contrib.staticfiles.storage import (
    StaticFilesStorage as DjangoStaticFilesStorage,
    ManifestStaticFilesStorage,
)

class StaticFilesStorage(DjangoStaticFilesStorage):
    """
    Auto select storage:
    - DEBUG = True  -> StaticFilesStorage
    - DEBUG = False -> ManifestStaticFilesStorage
    
    ## For Django 4.2+
    STORAGES = {
        "default": {
            "BACKEND": "django_object_storage.staticfiles.StaticFilesStorage",
        },
    }

    ## For Django versions below 4.2
    DEFAULT_FILE_STORAGE = "django_object_storage.staticfiles.StaticFilesStorage"
    """

    def __new__(cls, *args, **kwargs):
        if settings.DEBUG:
            return StaticFilesStorage(*args, **kwargs)
        return ManifestStaticFilesStorage(*args, **kwargs)