from __future__ import annotations
__all__ = ['TracebackJob']
from typing import TYPE_CHECKING
import uuid
from minfx.neptune_v2.attributes.constants import SYSTEM_FAILED_ATTRIBUTE_PATH
from minfx.neptune_v2.internal.background_job import BackgroundJob
from minfx.neptune_v2.internal.utils.logger import get_logger
from minfx.neptune_v2.internal.utils.uncaught_exception_handler import instance as traceback_handler
_logger = get_logger()

class TracebackJob(BackgroundJob):

    def __init__(self, path, fail_on_exception=True):
        self._uuid = uuid.uuid4()
        self._started = False
        self._path = path
        self._fail_on_exception = fail_on_exception

    def start(self, container):
        if not self._started:
            path = self._path
            fail_on_exception = self._fail_on_exception

            def log_traceback(stacktrace_lines):
                container[path].log(stacktrace_lines)
                if fail_on_exception:
                    container[SYSTEM_FAILED_ATTRIBUTE_PATH] = True
            traceback_handler.register(self._uuid, log_traceback)
        self._started = True

    def stop(self):
        traceback_handler.unregister(self._uuid)

    def join(self, seconds=None):
        pass

    def pause(self):
        pass

    def resume(self):
        pass