from datetime import timedelta
from storages.backends.gcloud import GoogleCloudStorage
from storages.utils import (
    setting,
)


class PublicGoogleCloudStorage(GoogleCloudStorage):
    def get_default_settings(self):
        return {
            "project_id": setting('GS_PROJECT_ID'),
            "credentials": setting('GS_CREDENTIALS'),
            "bucket_name": setting('GS_PUBLIC_BUCKET_NAME'),
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