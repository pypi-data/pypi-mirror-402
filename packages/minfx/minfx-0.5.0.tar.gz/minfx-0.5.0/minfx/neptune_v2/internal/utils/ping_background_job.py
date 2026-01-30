from __future__ import annotations
__all__ = ['PingBackgroundJob']
from typing import TYPE_CHECKING
from minfx.neptune_v2.internal.background_job import BackgroundJob
from minfx.neptune_v2.internal.threading.daemon import Daemon
from minfx.neptune_v2.internal.utils.logger import get_logger
_logger = get_logger()

class PingBackgroundJob(BackgroundJob):

    def __init__(self, period=10):
        self._period = period
        self._thread = None
        self._started = False

    def start(self, container):
        self._thread = self.ReportingThread(self._period, container)
        self._thread.start()
        self._started = True

    def stop(self):
        if not self._started:
            return
        self._thread.interrupt()

    def pause(self):
        self._thread.pause()

    def resume(self):
        self._thread.resume()

    def join(self, seconds=None):
        if not self._started:
            return
        self._thread.join(seconds)

    class ReportingThread(Daemon):

        def __init__(self, period, container):
            super().__init__(sleep_time=period, name='NeptunePing')
            self._container = container

        @Daemon.ConnectionRetryWrapper(kill_message="Killing Neptune ping thread. Your run's status will not be updated and the run will be shown as inactive.")
        def work(self):
            self._container.ping()