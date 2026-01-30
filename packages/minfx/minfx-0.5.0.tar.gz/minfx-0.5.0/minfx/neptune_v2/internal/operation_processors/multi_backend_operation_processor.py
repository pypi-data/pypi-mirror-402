from __future__ import annotations
__all__ = ('MultiBackendOperationProcessor',)
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait as futures_wait
from pathlib import Path
from typing import TYPE_CHECKING
from minfx.neptune_v2.constants import ASYNC_DIRECTORY
from minfx.neptune_v2.internal.operation import Operation
from minfx.neptune_v2.internal.operation import UploadFile
from minfx.neptune_v2.internal.operation_processors.async_operation_processor import AsyncOperationProcessor
from minfx.neptune_v2.internal.operation_processors.operation_processor import OperationProcessor
from minfx.neptune_v2.internal.operation_processors.utils import get_container_full_path
from minfx.neptune_v2.internal.utils.backend_name import backend_name_from_url
from minfx.neptune_v2.internal.utils.logger import get_logger
logger = get_logger()

class MultiBackendOperationProcessor(OperationProcessor):

    def __init__(self, container_id, container_type, multi_backend, lock, queue, sleep_time=3, batch_size=2048):
        self._container_id = container_id
        self._container_type = container_type
        self._lock = lock
        self._multi_backend = multi_backend
        backend_states = multi_backend._backend_states
        self._backend_indices = [state.index for state in backend_states]
        self._backend_addresses = {state.index: state.backend.get_display_address() for state in backend_states}
        base_path = get_container_full_path(ASYNC_DIRECTORY, container_id, container_type)
        if len(backend_states) > 1:
            logger.info('Multi-backend configuration:')
            for state in backend_states:
                logger.info(f'  [backend {state.index}] {state.backend.get_display_address()}')
        self._processors = []
        for state in backend_states:
            original_index = state.index
            backend_url = state.backend.get_display_address()
            backend_name = backend_name_from_url(backend_url)
            backend_path = base_path / backend_name
            processor = AsyncOperationProcessor(container_id=container_id, container_type=container_type, backend=state.backend, lock=threading.RLock(), queue=queue, sleep_time=sleep_time, batch_size=batch_size, data_path=backend_path, should_print_logs=True, backend_index=original_index, backend_address=backend_url)
            self._processors.append(processor)
        self._primary_processor = self._processors[0]

    @property
    def _consumer(self):
        return self._primary_processor._consumer

    def _backend_id(self, processor_position):
        original_index = self._backend_indices[processor_position]
        return f'[backend {original_index}] ({self._backend_addresses[original_index]})'

    @property
    def operation_storage(self):
        return self._primary_processor.operation_storage

    @property
    def data_path(self):
        return self._primary_processor.data_path

    def enqueue_operation(self, op, *, wait):
        if isinstance(op, UploadFile) and op.tmp_file_name:
            self._replicate_upload_file(op)
        for processor in self._processors:
            processor.enqueue_operation(op, wait=wait)

    def _replicate_upload_file(self, op):
        primary_storage = self._primary_processor.operation_storage
        source_path = Path(primary_storage.upload_path) / op.tmp_file_name
        if not source_path.exists():
            return
        for processor in self._processors[1:]:
            dest_path = Path(processor.operation_storage.upload_path) / op.tmp_file_name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)

    def start(self):
        for processor in self._processors:
            processor.start()

    def pause(self):
        for processor in self._processors:
            processor.pause()

    def resume(self):
        for processor in self._processors:
            processor.resume()

    def flush(self):
        if len(self._processors) > 1:
            logger.debug(f'Flushing buffers for {len(self._processors)} backend processors')
        for processor in self._processors:
            processor.flush()

    def wait(self):
        if len(self._processors) == 1:
            self._processors[0].wait()
            return
        try:
            with ThreadPoolExecutor(max_workers=len(self._processors)) as executor:
                futures = [executor.submit(p.wait) for p in self._processors]
                futures_wait(futures)
        except RuntimeError as e:
            if 'interpreter shutdown' not in str(e):
                raise
            for p in self._processors:
                p.wait()

    def stop(self, seconds=None):
        if len(self._processors) == 1:
            self._processors[0].stop(seconds)
            self._update_multi_backend_health()
            return
        logger.info(f'Synchronizing {len(self._processors)} backends...')
        try:
            with ThreadPoolExecutor(max_workers=len(self._processors)) as executor:
                futures = [executor.submit(p.stop, seconds) for p in self._processors]
                futures_wait(futures)
        except RuntimeError as e:
            if 'interpreter shutdown' not in str(e):
                raise
            for p in self._processors:
                p.stop(seconds)
        self._update_multi_backend_health()

    def _update_multi_backend_health(self):
        for i, processor in enumerate(self._processors):
            if hasattr(processor, '_consumer') and processor._consumer.last_backoff_time > 0:
                original_index = self._backend_indices[i]
                self._multi_backend.mark_backend_disconnected(original_index, Exception('Connection issues during sync'))

    def close(self):
        for processor in self._processors:
            processor.close()