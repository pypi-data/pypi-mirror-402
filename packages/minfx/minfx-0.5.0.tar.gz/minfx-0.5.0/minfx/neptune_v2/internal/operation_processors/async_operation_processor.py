from __future__ import annotations
__all__ = ('AsyncOperationProcessor',)
import contextlib
import os
import threading
from pathlib import Path
from time import monotonic, time
from typing import TYPE_CHECKING, Any
from minfx.neptune_v2.common.backends.utils import register_queue_size_provider, unregister_queue_size_provider
from minfx.neptune_v2.common.warnings import NeptuneWarning, warn_once
from minfx.neptune_v2.constants import ASYNC_DIRECTORY
from minfx.neptune_v2.core.components.abstract import WithResources
from minfx.neptune_v2.core.components.metadata_file import MetadataFile
from minfx.neptune_v2.core.components.operation_storage import OperationStorage
from minfx.neptune_v2.core.components.queue.disk_queue import DiskQueue, InMemoryQueue
from minfx.neptune_v2.envs import NEPTUNE_IN_MEMORY_QUEUE, NEPTUNE_SYNC_AFTER_STOP_TIMEOUT
from minfx.neptune_v2.exceptions import NeptuneSynchronizationAlreadyStoppedException
from minfx.neptune_v2.internal.init.parameters import DEFAULT_STOP_TIMEOUT
from minfx.neptune_v2.internal.operation import Operation
from minfx.neptune_v2.internal.operation_processors.operation_logger import ProcessorStopLogger
from minfx.neptune_v2.internal.operation_processors.operation_processor import OperationProcessor
from minfx.neptune_v2.internal.operation_processors.utils import common_metadata, get_container_full_path
from minfx.neptune_v2.internal.signals_processing.utils import signal_batch_lag, signal_batch_processed, signal_batch_started
from minfx.neptune_v2.internal.state import OperationAcceptance
from minfx.neptune_v2.internal.threading.daemon import Daemon
from minfx.neptune_v2.internal.utils.disk_utilization import ensure_disk_not_overutilize
from minfx.neptune_v2.internal.utils.logger import get_logger
logger = get_logger()

def serializer(op):
    return op.to_dict()

class AsyncOperationProcessor(WithResources, OperationProcessor):
    STOP_QUEUE_STATUS_UPDATE_FREQ_SECONDS = 10.0
    STOP_QUEUE_MAX_TIME_NO_CONNECTION_SECONDS = float(os.getenv(NEPTUNE_SYNC_AFTER_STOP_TIMEOUT, DEFAULT_STOP_TIMEOUT))

    def __init__(self, container_id, container_type, backend, lock, queue, sleep_time=3, batch_size=2048, data_path=None, should_print_logs=True, backend_index=None, backend_address=None):
        self._should_print_logs = should_print_logs
        self._backend_index = backend_index
        self._data_path = data_path if data_path else get_container_full_path(ASYNC_DIRECTORY, container_id, container_type)
        self._data_path.mkdir(parents=True, exist_ok=True)
        metadata = common_metadata(mode='async', container_id=container_id, container_type=container_type)
        if backend_address:
            metadata['backendAddress'] = backend_address
        self._metadata_file = MetadataFile(data_path=self._data_path, metadata=metadata)
        self._operation_storage = OperationStorage(data_path=self._data_path)
        if os.environ.get(NEPTUNE_IN_MEMORY_QUEUE):
            logger.info('Using in-memory queue (NEPTUNE_IN_MEMORY_QUEUE is set)')
            self._queue = InMemoryQueue(lock=lock)
        else:
            self._queue = DiskQueue(data_path=self._data_path, to_dict=serializer, from_dict=Operation.from_dict, lock=lock)
        self._container_id = container_id
        self._container_type = container_type
        self._backend = backend
        self._batch_size = batch_size
        self._last_version = 0
        self._consumed_version = 0
        self._consumer = self.ConsumerThread(self, sleep_time, batch_size)
        self._lock = lock
        self._signals_queue = queue
        self._operation_acceptance = OperationAcceptance.ACCEPTING
        self._waiting_cond = threading.Condition(lock=lock)
        self._queue_threshold = 0

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
        if not self._operation_acceptance.is_accepting():
            warn_once('Not accepting operations', exception=NeptuneWarning)
            return
        self._last_version = self._queue.put(op)
        self._check_queue_backpressure()
        if self._check_queue_size():
            self._consumer.wake_up()
        if wait:
            self.wait()

    def start(self):
        register_queue_size_provider(self._backend_index, self._queue.size)
        self._consumer.start()

    def pause(self):
        self._consumer.pause()
        self.flush()

    def resume(self):
        self._consumer.resume()

    def wait(self):
        self.flush()
        waiting_for_version = self._last_version
        self._consumer.wake_up()
        with self._waiting_cond:
            self._waiting_cond.wait_for(lambda: self._consumed_version >= waiting_for_version or not self._consumer.is_running())
        if not self._consumer.is_running():
            raise NeptuneSynchronizationAlreadyStoppedException

    def _check_queue_size(self):
        return self._queue.size() > self._batch_size / 2
    QUEUE_BACKPRESSURE_THRESHOLD = 5000

    def _check_queue_backpressure(self):
        size = self._queue.size()
        current_threshold = size // self.QUEUE_BACKPRESSURE_THRESHOLD
        if current_threshold > self._queue_threshold:
            backend_prefix = f'[backend {self._backend_index}] ' if self._backend_index is not None else ''
            ops_queued = current_threshold * self.QUEUE_BACKPRESSURE_THRESHOLD
            logger.warning('%sQueue backpressure: %d ops queued (sync may be slower than logging)', backend_prefix, ops_queued)
            self._queue_threshold = current_threshold

    def _check_queue_backpressure_lifted(self):
        if self._queue_threshold == 0:
            return
        size = self._queue.size()
        if size < self.QUEUE_BACKPRESSURE_THRESHOLD:
            backend_prefix = f'[backend {self._backend_index}] ' if self._backend_index is not None else ''
            logger.info('%sQueue backpressure lifted (%d ops remaining)', backend_prefix, size)
            self._queue_threshold = 0

    def _wait_for_queue_empty(self, initial_queue_size, seconds, signal_queue=None):
        waiting_start = monotonic()
        time_elapsed = 0.0
        max_reconnect_wait_time = self.STOP_QUEUE_MAX_TIME_NO_CONNECTION_SECONDS if seconds is None else seconds
        op_logger = ProcessorStopLogger(processor_id=id(self), signal_queue=signal_queue, logger=logger, should_print_logs=self._should_print_logs, backend_index=self._backend_index, data_path=str(self._data_path), total_ops=self._last_version)
        if initial_queue_size > 0:
            if self._consumer.last_backoff_time > 0:
                op_logger.log_connection_interruption(max_reconnect_wait_time)
            else:
                op_logger.log_remaining_operations(size_remaining=initial_queue_size)
        while True:
            if seconds is None:
                if self._consumer.last_backoff_time == 0:
                    waiting_start = monotonic()
                remaining = max(max_reconnect_wait_time - time_elapsed, 0.0)
                wait_time = min(remaining, self.STOP_QUEUE_STATUS_UPDATE_FREQ_SECONDS)
            else:
                wait_time = max(min(seconds - time_elapsed, self.STOP_QUEUE_STATUS_UPDATE_FREQ_SECONDS), 0.0)
            self._queue.wait_for_empty(wait_time)
            size_remaining = self._queue.size()
            already_synced = initial_queue_size - size_remaining
            already_synced_proc = already_synced / initial_queue_size * 100 if initial_queue_size else 100
            if size_remaining == 0:
                op_logger.log_success(ops_synced=initial_queue_size)
                return
            time_elapsed = monotonic() - waiting_start
            if self._consumer.last_backoff_time > 0 and time_elapsed >= max_reconnect_wait_time:
                op_logger.log_reconnect_failure(max_reconnect_wait_time=max_reconnect_wait_time, size_remaining=size_remaining)
                return
            if seconds is not None and wait_time == 0:
                op_logger.log_sync_failure(seconds=seconds, size_remaining=size_remaining)
                return
            if not self._consumer.is_running():
                exception = NeptuneSynchronizationAlreadyStoppedException()
                logger.warning(str(exception))
                return
            op_logger.log_still_waiting(size_remaining=size_remaining, already_synced=already_synced, already_synced_proc=already_synced_proc, is_disconnected=self._consumer.last_backoff_time > 0)

    def stop(self, seconds=None, signal_queue=None):
        ts = time()
        self.flush()
        if self._consumer.is_running():
            self._consumer.disable_sleep()
            self._consumer.wake_up()
            self._wait_for_queue_empty(initial_queue_size=self._queue.size(), seconds=seconds, signal_queue=signal_queue)
            self._consumer.interrupt()
        sec_left = None if seconds is None else seconds - (time() - ts)
        self._consumer.join(sec_left)
        self.close()
        if self._queue.is_empty():
            self.cleanup()

    def cleanup(self):
        super().cleanup()
        with contextlib.suppress(OSError):
            self._data_path.rmdir()

    def close(self):
        self._operation_acceptance = OperationAcceptance.REJECTING
        unregister_queue_size_provider(self._backend_index)
        super().close()

    class ConsumerThread(Daemon):

        def __init__(self, processor, sleep_time, batch_size):
            super().__init__(sleep_time=sleep_time, name='NeptuneAsyncOpProcessor')
            self._processor = processor
            self._batch_size = batch_size
            self._last_flush = 0.0

        def run(self):
            try:
                super().run()
            except Exception:
                with self._processor._waiting_cond:
                    self._processor._waiting_cond.notify_all()
                raise

        def work(self):
            ts = time()
            if ts - self._last_flush >= self._sleep_time:
                self._last_flush = ts
                self._processor._queue.flush()
                logger.debug('Disk queue flushed to persistent storage')
            while True:
                batch = self._processor._queue.get_batch(self._batch_size)
                if not batch:
                    return
                signal_batch_started(queue=self._processor._signals_queue)
                self.process_batch([element.obj for element in batch], batch[-1].ver, batch[-1].at)

        def _handle_errors(self, errors):
            for error in errors:
                error_str = str(error)
                if 'sys/state is read only' in error_str:
                    logger.debug('Skipped setting sys/state (read-only on Neptune backend)')
                    continue
                logger.error('Error occurred during asynchronous operation processing: %s', error)

        @Daemon.ConnectionRetryWrapper(kill_message='Killing Minfx asynchronous thread. Unsynchronized data is saved on disk.')
        def process_batch(self, batch, version, occurred_at=None):
            if occurred_at is not None:
                signal_batch_lag(queue=self._processor._signals_queue, lag=time() - occurred_at)
            expected_count = len(batch)
            version_to_ack = version - expected_count
            while True:
                processed_count, errors = self._processor._backend.execute_operations(container_id=self._processor._container_id, container_type=self._processor._container_type, operations=batch, operation_storage=self._processor._operation_storage)
                signal_batch_processed(queue=self._processor._signals_queue)
                version_to_ack += processed_count
                batch = batch[processed_count:]
                with self._processor._waiting_cond:
                    self._processor._queue.ack(version_to_ack)
                    self._processor._check_queue_backpressure_lifted()
                    self._handle_errors(errors)
                    self._processor._consumed_version = version_to_ack
                    if version_to_ack == version:
                        self._processor._waiting_cond.notify_all()
                        return