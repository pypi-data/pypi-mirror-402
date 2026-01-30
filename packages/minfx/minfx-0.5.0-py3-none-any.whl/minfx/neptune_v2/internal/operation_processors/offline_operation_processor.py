from __future__ import annotations
__all__ = ('OfflineOperationProcessor',)
from pathlib import Path
from typing import TYPE_CHECKING, Any
from minfx.neptune_v2.constants import OFFLINE_DIRECTORY
from minfx.neptune_v2.core.components.abstract import WithResources
from minfx.neptune_v2.core.components.metadata_file import MetadataFile
from minfx.neptune_v2.core.components.operation_storage import OperationStorage
from minfx.neptune_v2.core.components.queue.disk_queue import DiskQueue
from minfx.neptune_v2.internal.operation import Operation
from minfx.neptune_v2.internal.operation_processors.operation_processor import OperationProcessor
from minfx.neptune_v2.internal.operation_processors.utils import common_metadata, get_container_full_path
from minfx.neptune_v2.internal.utils.disk_utilization import ensure_disk_not_overutilize

def serializer(op):
    return op.to_dict()

class OfflineOperationProcessor(WithResources, OperationProcessor):

    def __init__(self, container_id, container_type, lock):
        self._data_path = get_container_full_path(OFFLINE_DIRECTORY, container_id, container_type)
        self._data_path.mkdir(parents=True, exist_ok=True)
        self._metadata_file = MetadataFile(data_path=self._data_path, metadata=common_metadata(mode='offline', container_id=container_id, container_type=container_type))
        self._operation_storage = OperationStorage(data_path=self._data_path)
        self._queue = DiskQueue(data_path=self._data_path, to_dict=serializer, from_dict=Operation.from_dict, lock=lock)

    @property
    def operation_storage(self):
        return self._operation_storage

    @property
    def data_path(self):
        return self._data_path

    @property
    def resources(self):
        return (self._metadata_file, self._operation_storage, self._queue)

    @ensure_disk_not_overutilize
    def enqueue_operation(self, op, *, wait):
        self._queue.put(op)

    def wait(self):
        self.flush()

    def stop(self, seconds=None):
        self.flush()
        self.close()