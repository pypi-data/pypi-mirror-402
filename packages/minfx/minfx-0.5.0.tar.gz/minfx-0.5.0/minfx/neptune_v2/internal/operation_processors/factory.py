__all__ = ['get_operation_processor']
import os
import threading
from typing import TYPE_CHECKING
from minfx.neptune_v2.envs import NEPTUNE_ASYNC_BATCH_SIZE
from minfx.neptune_v2.internal.backends.multi_backend import MultiBackend
from minfx.neptune_v2.internal.backends.neptune_backend import NeptuneBackend
from minfx.neptune_v2.internal.container_type import ContainerType
from minfx.neptune_v2.internal.id_formats import UniqueId
from minfx.neptune_v2.types.mode import Mode
from .async_operation_processor import AsyncOperationProcessor
from .multi_backend_operation_processor import MultiBackendOperationProcessor
from .offline_operation_processor import OfflineOperationProcessor
from .operation_processor import OperationProcessor
from .read_only_operation_processor import ReadOnlyOperationProcessor
from .sync_operation_processor import SyncOperationProcessor

def build_async_operation_processor(container_id, container_type, backend, lock, sleep_time, queue):
    assert isinstance(backend, MultiBackend), 'Backend must be a MultiBackend'
    return MultiBackendOperationProcessor(container_id=container_id, container_type=container_type, multi_backend=backend, lock=lock, queue=queue, sleep_time=sleep_time, batch_size=int(os.environ.get(NEPTUNE_ASYNC_BATCH_SIZE) or '2048'))

def get_operation_processor(mode, container_id, container_type, backend, lock, flush_period, queue):
    if mode == Mode.ASYNC:
        return build_async_operation_processor(container_id=container_id, container_type=container_type, backend=backend, lock=lock, sleep_time=flush_period, queue=queue)
    if mode in (Mode.SYNC, Mode.DEBUG):
        return SyncOperationProcessor(container_id, container_type, backend)
    if mode == Mode.OFFLINE:
        return OfflineOperationProcessor(container_id, container_type, lock)
    if mode == Mode.READ_ONLY:
        return ReadOnlyOperationProcessor()
    raise ValueError(f'mode should be one of {list(Mode)}')