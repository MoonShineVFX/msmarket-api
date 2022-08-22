import json
import base64
import datetime as dt
from typing import Optional
from datetime import timedelta
from storages.backends.gcloud import GoogleCloudStorage
from storages.utils import (
    setting,
)

from google import auth
from google.cloud import storage
from google.oauth2 import service_account


def dict_to_base64(dict_obj):
    message_str = json.dumps(dict_obj)
    message_bytes = message_str.encode()
    base64_bytes = base64.b64encode(message_bytes)

    base64_message = base64_bytes.decode()
    return base64_message


def base64_to_dict(base64_obj):
    b64_str = base64_obj
    b64_str = b64_str.encode()
    b64_bytes = base64.b64decode(b64_str)
    decode_str = b64_bytes.decode()
    decode_dict = json.loads(decode_str)
    return decode_dict


def generate_signed_url_v2(file_path=None):
    service_account_info = base64_to_dict(setting('MEDIA_SERVICE_ACCOUNT_SECRET'))
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info)
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


def generate_session_uri_for_upload(file_path=None):
    service_account_info = base64_to_dict(setting('UPLOAD_SERVICE_ACCOUNT_SECRET'))
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info)

    bucket_name = setting('GS_INTERNAL_BUCKET_NAME')
    origin = "https://{}".format(setting('API_HOST'))

    content_type = "application/x-7z-compressed"
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(file_path)

    session_uri = blob.create_resumable_upload_session(content_type=content_type, origin=origin)

    return session_uri


def delete_model(file_path=None):
    service_account_info = base64_to_dict(setting('UPLOAD_SERVICE_ACCOUNT_SECRET'))
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info)
    bucket_name = setting('GS_INTERNAL_BUCKET_NAME')
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(file_path)
    try:
        blob.delete()
    except Exception as e:
        print(e)


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