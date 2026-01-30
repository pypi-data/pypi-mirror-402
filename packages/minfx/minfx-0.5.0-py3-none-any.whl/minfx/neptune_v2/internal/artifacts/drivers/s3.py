from __future__ import annotations
__all__ = ['S3ArtifactDriver']
from datetime import datetime
import pathlib
import typing
from urllib.parse import urlparse
from botocore.exceptions import NoCredentialsError
from minfx.neptune_v2.exceptions import NeptuneRemoteStorageAccessException, NeptuneRemoteStorageCredentialsException, NeptuneUnsupportedArtifactFunctionalityException
from minfx.neptune_v2.internal.artifacts.types import ArtifactDriver, ArtifactFileData, ArtifactFileType
from minfx.neptune_v2.internal.utils.s3 import get_boto_s3_client

class S3ArtifactDriver(ArtifactDriver):
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    @staticmethod
    def get_type():
        return ArtifactFileType.S3.value

    @classmethod
    def matches(cls, path):
        return urlparse(path).scheme == 's3'

    @classmethod
    def _serialize_metadata(cls, metadata):
        return {'location': metadata['location'], 'last_modified': metadata['last_modified'].strftime(cls.DATETIME_FORMAT)}

    @classmethod
    def _deserialize_metadata(cls, metadata):
        return {'location': metadata['location'], 'last_modified': datetime.strptime(metadata['last_modified'], cls.DATETIME_FORMAT)}

    @classmethod
    def get_tracked_files(cls, path, destination=None):
        url = urlparse(path)
        bucket_name, prefix = (url.netloc, url.path.lstrip('/'))
        if '*' in prefix:
            raise NeptuneUnsupportedArtifactFunctionalityException(f'Wildcard characters (*,?) in location URI ({path}) are not supported.')
        remote_storage = get_boto_s3_client().Bucket(bucket_name)
        stored_files = []
        try:
            for remote_object in remote_storage.objects.filter(Prefix=prefix):
                if prefix == remote_object.key:
                    prefix = str(pathlib.PurePosixPath(prefix).parent)
                remote_key = remote_object.key
                destination = pathlib.PurePosixPath(destination or '')
                relative_file_path = remote_key[len(prefix.lstrip('.')):].lstrip('/')
                file_path = destination / relative_file_path
                stored_files.append(ArtifactFileData(file_path=str(file_path).lstrip('/'), file_hash=remote_object.e_tag.strip('"'), type=ArtifactFileType.S3.value, size=remote_object.size, metadata=cls._serialize_metadata({'location': f"s3://{bucket_name}/{remote_key.lstrip('/')}", 'last_modified': remote_object.last_modified})))
        except NoCredentialsError:
            raise NeptuneRemoteStorageCredentialsException
        except (remote_storage.meta.client.exceptions.NoSuchBucket, remote_storage.meta.client.exceptions.NoSuchKey):
            raise NeptuneRemoteStorageAccessException(location=path)
        return stored_files

    @classmethod
    def download_file(cls, destination, file_definition):
        location = file_definition.metadata.get('location')
        url = urlparse(location)
        bucket_name, path = (url.netloc, url.path.lstrip('/'))
        remote_storage = get_boto_s3_client()
        try:
            bucket = remote_storage.Bucket(bucket_name)
            bucket.download_file(path, str(destination))
        except NoCredentialsError:
            raise NeptuneRemoteStorageCredentialsException
        except (remote_storage.meta.client.exceptions.NoSuchBucket, remote_storage.meta.client.exceptions.NoSuchKey):
            raise NeptuneRemoteStorageAccessException(location=location)