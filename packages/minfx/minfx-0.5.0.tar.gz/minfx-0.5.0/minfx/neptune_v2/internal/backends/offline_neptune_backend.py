from __future__ import annotations
__all__ = ['OfflineNeptuneBackend']
from typing import TYPE_CHECKING
from minfx.neptune_v2.exceptions import NeptuneOfflineModeFetchException
from minfx.neptune_v2.internal.backends.neptune_backend_mock import NeptuneBackendMock

class OfflineNeptuneBackend(NeptuneBackendMock):
    WORKSPACE_NAME = 'offline'

    def get_attributes(self, container_id, container_type):
        raise NeptuneOfflineModeFetchException

    def get_float_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def get_int_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def get_bool_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def get_file_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def get_string_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def get_datetime_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def get_artifact_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def list_artifact_files(self, project_id, artifact_hash):
        raise NeptuneOfflineModeFetchException

    def get_float_series_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def get_string_series_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def get_string_set_attribute(self, container_id, container_type, path):
        raise NeptuneOfflineModeFetchException

    def get_string_series_values(self, container_id, container_type, path, offset, limit):
        raise NeptuneOfflineModeFetchException

    def get_float_series_values(self, container_id, container_type, path, offset, limit):
        raise NeptuneOfflineModeFetchException

    def get_image_series_values(self, container_id, container_type, path, offset, limit):
        raise NeptuneOfflineModeFetchException

    def download_file_series_by_index(self, container_id, container_type, path, index, destination, progress_bar):
        raise NeptuneOfflineModeFetchException

    def list_fileset_files(self, attribute, container_id, path):
        raise NeptuneOfflineModeFetchException