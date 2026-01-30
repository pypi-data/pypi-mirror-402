from __future__ import annotations
__all__ = ['CallbacksMonitor']
from typing import TYPE_CHECKING, Callable
from minfx.neptune_v2.internal.background_job import BackgroundJob
from minfx.neptune_v2.internal.signals_processing.signals_processor import SignalsProcessor

class CallbacksMonitor(BackgroundJob):

    def __init__(self, queue, async_lag_threshold, async_no_progress_threshold, async_lag_callback=None, async_no_progress_callback=None, period=10):
        self._period = period
        self._queue = queue
        self._thread = None
        self._started = False
        self._async_lag_threshold = async_lag_threshold
        self._async_no_progress_threshold = async_no_progress_threshold
        self._async_lag_callback = async_lag_callback
        self._async_no_progress_callback = async_no_progress_callback

    def start(self, container):
        self._thread = SignalsProcessor(period=self._period, container=container, queue=self._queue, async_lag_threshold=self._async_lag_threshold, async_no_progress_threshold=self._async_no_progress_threshold, async_lag_callback=self._async_lag_callback, async_no_progress_callback=self._async_no_progress_callback)
        self._thread.start()
        self._started = True

    def stop(self):
        if self._thread and self._started:
            self._thread.interrupt()

    def join(self, seconds=None):
        if self._thread and self._started:
            self._thread.join(seconds)

    def pause(self):
        if self._thread:
            self._thread.pause()

    def resume(self):
        if self._thread:
            self._thread.resume()