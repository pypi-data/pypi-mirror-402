from __future__ import annotations
__all__ = ['SignalsProcessor']
from queue import Empty, Queue
from threading import Thread
from time import monotonic
from typing import TYPE_CHECKING, Callable
from minfx.neptune_v2.internal.init.parameters import IN_BETWEEN_CALLBACKS_MINIMUM_INTERVAL
from minfx.neptune_v2.internal.signals_processing.signals import BatchLagSignal, SignalsVisitor
from minfx.neptune_v2.internal.threading.daemon import Daemon

class SignalsProcessor(Daemon, SignalsVisitor):

    def __init__(self, *, period, container, queue, async_lag_threshold, async_no_progress_threshold, async_lag_callback=None, async_no_progress_callback=None, callbacks_interval=IN_BETWEEN_CALLBACKS_MINIMUM_INTERVAL, in_async=True):
        super().__init__(sleep_time=period, name='CallbacksMonitor')
        self._container = container
        self._queue = queue
        self._async_lag_threshold = async_lag_threshold
        self._async_no_progress_threshold = async_no_progress_threshold
        self._async_lag_callback = async_lag_callback
        self._async_no_progress_callback = async_no_progress_callback
        self._callbacks_interval = callbacks_interval
        self._in_async = in_async
        self._last_batch_started_at = None
        self._last_no_progress_callback_at = None
        self._last_lag_callback_at = None

    def visit_batch_started(self, signal):
        if self._last_batch_started_at is None:
            self._last_batch_started_at = signal.occured_at

    def visit_batch_processed(self, signal):
        if self._last_batch_started_at is not None:
            self._check_no_progress(at_timestamp=signal.occured_at)
            self._last_batch_started_at = None

    def visit_batch_lag(self, signal):
        if self._async_lag_callback is None or not isinstance(signal, BatchLagSignal):
            return
        if signal.lag > self._async_lag_threshold:
            current_time = monotonic()
            if self._last_lag_callback_at is None or current_time - self._last_lag_callback_at > self._callbacks_interval:
                execute_callback(callback=self._async_lag_callback, container=self._container, in_async=self._in_async)
                self._last_lag_callback_at = current_time

    def _check_callbacks(self):
        self._check_no_progress(at_timestamp=monotonic())

    def _check_no_progress(self, at_timestamp):
        if self._async_no_progress_callback is None:
            return
        if self._last_batch_started_at is not None:
            if at_timestamp - self._last_batch_started_at > self._async_no_progress_threshold and (self._last_no_progress_callback_at is None or at_timestamp - self._last_no_progress_callback_at > self._callbacks_interval):
                execute_callback(callback=self._async_no_progress_callback, container=self._container, in_async=self._in_async)
                self._last_no_progress_callback_at = monotonic()

    def work(self):
        try:
            while not self._queue.empty():
                signal = self._queue.get_nowait()
                signal.accept(self)
            self._check_callbacks()
        except Empty:
            pass

def execute_callback(*, callback, container, in_async):
    if in_async:
        Thread(target=callback, name='CallbackExecution', args=(container,), daemon=True).start()
    else:
        callback(container)