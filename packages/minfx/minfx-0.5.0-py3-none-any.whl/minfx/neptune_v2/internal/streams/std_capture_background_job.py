from __future__ import annotations
__all__ = ['StderrCaptureBackgroundJob', 'StdoutCaptureBackgroundJob']
from typing import TYPE_CHECKING
from minfx.neptune_v2.internal.background_job import BackgroundJob
from minfx.neptune_v2.internal.streams.std_stream_capture_logger import StderrCaptureLogger, StdoutCaptureLogger

class StdoutCaptureBackgroundJob(BackgroundJob):

    def __init__(self, attribute_name):
        self._attribute_name = attribute_name
        self._logger = None

    def start(self, container):
        self._logger = StdoutCaptureLogger(container, self._attribute_name)

    def stop(self):
        self._logger.close()

    def pause(self):
        self._logger.pause()

    def resume(self):
        self._logger.resume()

    def join(self, seconds=None):
        pass

class StderrCaptureBackgroundJob(BackgroundJob):

    def __init__(self, attribute_name):
        self._attribute_name = attribute_name
        self._logger = None

    def start(self, container):
        self._logger = StderrCaptureLogger(container, self._attribute_name)

    def stop(self):
        self._logger.close()

    def pause(self):
        self._logger.pause()

    def resume(self):
        self._logger.resume()

    def join(self, seconds=None):
        pass