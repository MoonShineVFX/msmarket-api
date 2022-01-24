import sys
import datetime as dt
from six.moves import urllib
from datetime import timedelta
from storages.backends.gcloud import GoogleCloudStorage
from storages.utils import (
    setting,
)

from google import auth
from google.cloud import storage


def get_download_link(file_path=None):
    SCOPES = [
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/cloud-platform"
    ]

    credentials, project = auth.default(
        scopes=SCOPES
    )
    credentials.refresh(auth.transport.requests.Request())
    expiration_timedelta = dt.timedelta(days=7)
    bucket_name = setting('GS_INTERNAL_BUCKET_NAME')
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(file_path)
    if blob:
        signed_url = blob.generate_signed_url(
            expiration=expiration_timedelta,
            service_account_email=credentials.service_account_email,
            access_token=credentials.token,
        )
    else:
        signed_url = None
    return signed_url


class PublicGoogleCloudStorage(GoogleCloudStorage):
    def get_default_settings(self):
        return {
            "project_id": setting('GS_PROJECT_ID'),
            "credentials": setting('GS_CREDENTIALS'),
            "bucket_name": setting('GS_BUCKET_NAME'),
            "custom_endpoint": setting('GS_CUSTOM_ENDPOINT', None),
            "location": setting('GS_LOCATION', ''),
            "default_acl": setting('GS_DEFAULT_ACL'),
            "querystring_auth": setting('GS_QUERYSTRING_AUTH', True),
            "expiration": setting('GS_EXPIRATION', timedelta(seconds=86400)),
            "file_overwrite": setting('GS_FILE_OVERWRITE', True),
            "cache_control": setting('GS_CACHE_CONTROL'),
            # The max amount of memory a returned file can take up before being
            # rolled over into a temporary file on disk. Default is 0: Do not
            # roll over.
            "max_memory_size": setting('GS_MAX_MEMORY_SIZE', 0),
            "blob_chunk_size": setting('GS_BLOB_CHUNK_SIZE'),
        }