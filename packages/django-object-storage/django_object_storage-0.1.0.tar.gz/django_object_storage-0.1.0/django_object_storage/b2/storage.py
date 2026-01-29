import base64
from io import BytesIO
from tempfile import TemporaryFile

from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
import requests
import urllib


class BackBlazeB2(object):
    def __init__(self, app_key=None, account_id=None, bucket_name=None, bucket_id=None):
        self.bucket_id = bucket_id
        self.account_id = account_id
        self.app_key = app_key
        self.bucket_name = bucket_name
        self.base_url = ""
        self.authorization_token = ""
        self.download_url = ""
        self.authorize()

    def authorize(self):
        try:
            auth_string = f"{self.account_id}:{self.app_key}"
            encoded_auth_string = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
            basic_auth_header = f"Basic {encoded_auth_string}"
            headers = {"Authorization": basic_auth_header}

            response = requests.get("https://api.backblaze.com/b2api/v2/b2_authorize_account", headers=headers)
            response.raise_for_status()

            if response.status_code == 200:
                resp = response.json()
                self.base_url = resp["apiUrl"]
                self.download_url = resp["downloadUrl"]
                self.authorization_token = resp["authorizationToken"]
                return True
            else:
                return False
        except requests.RequestException as e:
            return False

    def get_upload_url(self):
        params = {"bucketId": self.bucket_id}
        url = self._build_url("/b2api/v1/b2_get_upload_url")
        headers = {"Authorization": self.authorization_token}
        return requests.get(url, headers=headers, params=params).json()

    def _build_url(self, endpoint=None, authorization=True):
        return "%s%s" % (self.base_url, endpoint)

    def normalize_filename(self, name):
        parts = name.replace("\\", "/").split("/")
        return "/".join([urllib.parse.quote(part, safe="") for part in parts])

    def upload_file(self, name, content):
        response = self.get_upload_url()
        if "uploadUrl" not in response:
            self.authorize()
            response = self.get_upload_url()
            if "uploadUrl" not in response:
                return False

        content.seek(0)

        upload_url = response["uploadUrl"]
        normalized_name = self.normalize_filename(name)

        headers = {
            "Authorization": response["authorizationToken"],
            "X-Bz-File-Name": normalized_name,
            "Content-Type": "b2/x-auto",
            "X-Bz-Content-Sha1": "do_not_verify",
            "X-Bz-Info-src_last_modified_millis": "",
        }
        download_response = requests.post(upload_url, headers=headers, data=content.read())

        if download_response.status_code == 503:
            attempts = 0
            while attempts <= 3 and download_response.status_code == 503:
                download_response = requests.post(upload_url, headers=headers, data=content.read())
                attempts += 1

        if download_response.status_code != 200:
            download_response.raise_for_status()

        return download_response.json()

    def get_file_info(self, name):
        headers = {"Authorization": self.authorization_token}
        normalized_name = self.normalize_filename(name)
        return requests.get(
            "%s/file/%s/%s" % (self.download_url, self.bucket_name, normalized_name),
            headers=headers,
        )

    def download_file(self, name):
        headers = {"Authorization": self.authorization_token}
        normalized_name = self.normalize_filename(name)
        return requests.get(
            "%s/file/%s/%s" % (self.download_url, self.bucket_name, normalized_name),
            headers=headers,
        ).content

    def get_file_url(self, name):
        normalized_name = self.normalize_filename(name)
        return "%s/file/%s/%s" % (self.download_url, self.bucket_name, normalized_name)

    def get_bucket_id_by_name(self):
        headers = {"Authorization": self.authorization_token}
        params = {"accountId": self.account_id}
        resp = requests.get(
            self._build_url("/b2api/v1/b2_list_buckets"),
            headers=headers,
            params=params,
        ).json()

        if "buckets" in resp:
            buckets = resp["buckets"]
            for bucket in buckets:
                if bucket["bucketName"] == self.bucket_name:
                    self.bucket_id = bucket["bucketId"]
                    return True
        else:
            return False


@deconstructible
class B2Storage(Storage):
    """# Django Storage: BackBlazeB2.

    Reads configuration from Django settings when not provided explicitly:
    - STORAGE_B2_APP_KEY
    - STORAGE_B2_ACCOUNT_ID
    - STORAGE_B2_BUCKET_NAME
    - STORAGE_B2_BUCKET_ID

    ## For Django 4.2+
    STORAGES = {
        "default": {
            "BACKEND": "django_object_storage.b2.B2Storage",
        },
    }

    ## Or with options
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

    ## For Django versions below 4.2
    DEFAULT_FILE_STORAGE = "django_object_storage.b2.B2Storage"
    """

    def __init__(self, account_id=None, app_key=None, bucket_name=None, bucket_id=None):
        from django.conf import settings

        app_key = app_key or getattr(settings, "STORAGE_B2_APP_KEY", None)
        account_id = account_id or getattr(settings, "STORAGE_B2_ACCOUNT_ID", None)
        bucket_name = bucket_name or getattr(settings, "STORAGE_B2_BUCKET_NAME", None)
        bucket_id = bucket_id or getattr(settings, "STORAGE_B2_BUCKET_ID", None)

        self.b2 = BackBlazeB2(app_key, account_id, bucket_name, bucket_id)

    def save(self, name, content, max_length=None):
        resp = self.b2.upload_file(name, content)
        if "fileName" in resp:
            return resp["fileName"]
        return None

    def exists(self, name):
        return False

    def _temporary_storage(self, contents):
        conent_file = TemporaryFile(contents, "r+")
        return conent_file

    def open(self, name, mode="rb"):
        resp = self.b2.download_file(name)

        output = BytesIO()
        output.write(resp)
        output.seek(0)
        return File(output, name)

    def url(self, name):
        return self.b2.get_file_url(name)
