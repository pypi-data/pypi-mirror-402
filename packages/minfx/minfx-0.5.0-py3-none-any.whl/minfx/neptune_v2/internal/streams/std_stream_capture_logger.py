from __future__ import annotations
__all__ = ['StderrCaptureLogger', 'StdoutCaptureLogger']
from queue import Queue
import sys
import threading
from typing import TYPE_CHECKING, TextIO
from minfx.neptune_v2.internal.threading.daemon import Daemon
from minfx.neptune_v2.logging import Logger as NeptuneLogger

class StdStreamCaptureLogger:

    def __init__(self, container, attribute_name, stream):
        self._logger = NeptuneLogger(container, attribute_name)
        self.stream = stream
        self._thread_local = threading.local()
        self.enabled = True
        self._log_data_queue = Queue()
        self._logging_thread = self.ReportingThread(self, 'NeptuneThread_' + attribute_name)
        self._logging_thread.start()

    def pause(self):
        self._log_data_queue.put_nowait(None)
        self._logging_thread.pause()

    def resume(self):
        self._logging_thread.resume()

    def write(self, data):
        self.stream.write(data)
        self._log_data_queue.put_nowait(data)

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

    def close(self):
        if self.enabled:
            self._logging_thread.interrupt()
        self.enabled = False
        self._log_data_queue.put_nowait(None)
        self._logging_thread.join()

    class ReportingThread(Daemon):

        def __init__(self, logger, name):
            super().__init__(sleep_time=0, name=name)
            self._logger = logger

        @Daemon.ConnectionRetryWrapper(kill_message='Killing Neptune STD capturing thread.')
        def work(self):
            while True:
                data = self._logger._log_data_queue.get()
                if data is None:
                    break
                self._logger._logger.log(data)

class StdoutCaptureLogger(StdStreamCaptureLogger):

    def __init__(self, container, attribute_name):
        super().__init__(container, attribute_name, sys.stdout)
        sys.stdout = self

    def close(self):
        sys.stdout = self.stream
        super().close()

class StderrCaptureLogger(StdStreamCaptureLogger):

    def __init__(self, container, attribute_name):
        super().__init__(container, attribute_name, sys.stderr)
        sys.stderr = self

    def close(self, wait_for_all_logs=True):
        sys.stderr = self.stream
        super().close()