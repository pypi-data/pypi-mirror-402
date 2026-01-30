from __future__ import annotations
__all__ = ['instance']
from platform import node as get_hostname
import sys
import threading
import traceback
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Optional, Type
from minfx.neptune_v2.internal.utils.logger import get_logger
_logger = get_logger()
SYS_UNCAUGHT_EXCEPTION_HANDLER_TYPE = Callable[[Type[BaseException], BaseException, Optional[TracebackType]], Any]

class UncaughtExceptionHandler:

    def __init__(self):
        self._previous_uncaught_exception_handler = None
        self._handlers = {}
        self._lock = threading.Lock()
        self._last_exception_type = None

    def trigger(self, exc_type, exc_val, exc_tb):
        header_lines = [f'An uncaught exception occurred while run was active on worker {get_hostname()}.', 'Marking run as failed', 'Traceback:']
        traceback_lines = header_lines + traceback.format_tb(exc_tb) + str(exc_val).split('\n')
        for handler in self._handlers.values():
            handler(traceback_lines)

    def activate(self):
        with self._lock:
            if self._previous_uncaught_exception_handler is not None:
                return
            self._previous_uncaught_exception_handler = sys.excepthook
            sys.excepthook = self.exception_handler

    def deactivate(self):
        with self._lock:
            if self._previous_uncaught_exception_handler is None:
                return
            sys.excepthook = self._previous_uncaught_exception_handler
            self._previous_uncaught_exception_handler = None

    def register(self, uid, handler):
        with self._lock:
            self._handlers[uid] = handler

    def unregister(self, uid):
        with self._lock:
            if uid in self._handlers:
                del self._handlers[uid]

    def exception_handler(self, *args, **kwargs):
        if args:
            self._last_exception_type = args[0]
        self.trigger(*args, **kwargs)
        if self._previous_uncaught_exception_handler is not None:
            self._previous_uncaught_exception_handler(*args, **kwargs)

    def get_shutdown_reason(self):
        if self._last_exception_type is None:
            return 'completed'
        if self._last_exception_type is KeyboardInterrupt:
            return 'interrupted'
        return f'exception ({self._last_exception_type.__name__})'
instance = UncaughtExceptionHandler()