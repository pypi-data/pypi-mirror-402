from __future__ import annotations
__all__ = ('SyncOperationProcessor',)
import contextlib
from pathlib import Path
from typing import TYPE_CHECKING
from minfx.neptune_v2.constants import SYNC_DIRECTORY
from minfx.neptune_v2.core.components.abstract import WithResources
from minfx.neptune_v2.core.components.metadata_file import MetadataFile
from minfx.neptune_v2.core.components.operation_storage import OperationStorage
from minfx.neptune_v2.internal.operation_processors.operation_processor import OperationProcessor
from minfx.neptune_v2.internal.operation_processors.utils import common_metadata, get_container_full_path
from minfx.neptune_v2.internal.utils.disk_utilization import ensure_disk_not_overutilize

class SyncOperationProcessor(WithResources, OperationProcessor):

    def __init__(self, container_id, container_type, backend):
        self._container_id = container_id
        self._container_type = container_type
        self._backend = backend
        self._data_path = get_container_full_path(SYNC_DIRECTORY, container_id, container_type)
        self._data_path.mkdir(parents=True, exist_ok=True)
        self._metadata_file = MetadataFile(data_path=self._data_path, metadata=common_metadata(mode='sync', container_id=container_id, container_type=container_type))
        self._operation_storage = OperationStorage(data_path=self._data_path)

    @property
    def operation_storage(self):
        return self._operation_storage

    @property
    def data_path(self):
        return self._data_path

    @property
    def resources(self):
        return (self._metadata_file, self._operation_storage)

    @ensure_disk_not_overutilize
    def enqueue_operation(self, op, *, wait):
        _, errors = self._backend.execute_operations(container_id=self._container_id, container_type=self._container_type, operations=[op], operation_storage=self._operation_storage)
        if errors:
            raise errors[0]

    def stop(self, seconds=None):
        self.flush()
        self.close()
        self.cleanup()

    def cleanup(self):
        super().cleanup()
        with contextlib.suppress(OSError):
            self._data_path.rmdir()