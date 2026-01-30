from __future__ import annotations
__all__ = ['Daemon']
import abc
from enum import Enum
import functools
import threading
from typing import Any, Callable, TypeVar
R = TypeVar('R')
from minfx.neptune_v2.common.exceptions import NeptuneConnectionLostException
from minfx.neptune_v2.common.warnings import NeptuneWarning, warn_once
from minfx.neptune_v2.internal.utils.logger import get_logger
logger = get_logger()

class Daemon(threading.Thread):

    class DaemonState(Enum):
        INIT = 1
        WORKING = 2
        PAUSING = 3
        PAUSED = 4
        INTERRUPTED = 5
        STOPPED = 6

        def is_running(self):
            return self in {Daemon.DaemonState.WORKING, Daemon.DaemonState.PAUSING, Daemon.DaemonState.PAUSED}

        def is_terminal(self):
            return self in {Daemon.DaemonState.INTERRUPTED, Daemon.DaemonState.STOPPED}

    def __init__(self, sleep_time, name):
        super().__init__(daemon=True, name=name)
        self._sleep_time = sleep_time
        self._state = Daemon.DaemonState.INIT
        self._wait_condition = threading.Condition()
        self.last_backoff_time = 0

    def interrupt(self):
        with self._wait_condition:
            self._state = Daemon.DaemonState.INTERRUPTED
            self._wait_condition.notify_all()

    def pause(self):
        with self._wait_condition:
            if self._state != Daemon.DaemonState.PAUSED:
                if not self._is_interrupted():
                    self._state = Daemon.DaemonState.PAUSING
                self._wait_condition.notify_all()
                self._wait_condition.wait_for(lambda: self._state != Daemon.DaemonState.PAUSING)

    def resume(self):
        with self._wait_condition:
            if not self._is_interrupted():
                self._state = Daemon.DaemonState.WORKING
            self._wait_condition.notify_all()

    def wake_up(self):
        with self._wait_condition:
            self._wait_condition.notify_all()

    def disable_sleep(self):
        self._sleep_time = 0

    def is_running(self):
        with self._wait_condition:
            return self._state.is_running()

    def _is_interrupted(self):
        with self._wait_condition:
            return self._state.is_terminal()

    def run(self):
        with self._wait_condition:
            if not self._is_interrupted():
                self._state = Daemon.DaemonState.WORKING
        try:
            while not self._is_interrupted():
                with self._wait_condition:
                    if self._state == Daemon.DaemonState.PAUSING:
                        self._state = Daemon.DaemonState.PAUSED
                        self._wait_condition.notify_all()
                        self._wait_condition.wait_for(lambda: self._state != Daemon.DaemonState.PAUSED)
                if self._state == Daemon.DaemonState.WORKING:
                    self.work()
                    with self._wait_condition:
                        if self._sleep_time > 0 and self._state == Daemon.DaemonState.WORKING:
                            self._wait_condition.wait(timeout=self._sleep_time)
        finally:
            with self._wait_condition:
                self._state = Daemon.DaemonState.STOPPED
                self._wait_condition.notify_all()

    @abc.abstractmethod
    def work(self):
        pass

    class ConnectionRetryWrapper:
        INITIAL_RETRY_BACKOFF = 2
        MAX_RETRY_BACKOFF = 120

        def __init__(self, kill_message):
            self.kill_message = kill_message

        def __call__(self, func):

            @functools.wraps(func)
            def wrapper(self_, *args, **kwargs):
                while not self_._is_interrupted():
                    try:
                        result = func(self_, *args, **kwargs)
                        if self_.last_backoff_time > 0:
                            self_.last_backoff_time = 0
                            backend_prefix = ''
                            if hasattr(self_, '_processor') and hasattr(self_._processor, '_backend_index'):
                                idx = self_._processor._backend_index
                                if idx is not None:
                                    backend_prefix = f'[backend {idx}] '
                            logger.info('%sCommunication restored!', backend_prefix)
                        return result
                    except NeptuneConnectionLostException as e:
                        backend_prefix = ''
                        if hasattr(self_, '_processor') and hasattr(self_._processor, '_backend_index'):
                            idx = self_._processor._backend_index
                            if idx is not None:
                                backend_prefix = f'[backend {idx}] '
                        error_name = e.cause.__class__.__name__
                        if self_.last_backoff_time == 0:
                            if error_name == 'HTTPTooManyRequests':
                                warn_once("You're hitting the default logging-rate limit for your workspace. See how to optimize the logging calls to reduce requests: https://docs.neptune.ai/help/reducing_requests/. \n To increase the limits for your workspace, contact sales@neptune.ai.", exception=NeptuneWarning)
                            else:
                                logger.warning('%sConnection failed: %s. Retrying in %ss...', backend_prefix, error_name, self.INITIAL_RETRY_BACKOFF)
                            self_.last_backoff_time = self.INITIAL_RETRY_BACKOFF
                        else:
                            self_.last_backoff_time = min(self_.last_backoff_time * 2, self.MAX_RETRY_BACKOFF)
                            if not self_._is_interrupted():
                                logger.warning('%sConnection failed: %s. Retrying in %ss...', backend_prefix, error_name, self_.last_backoff_time)
                        with self_._wait_condition:
                            self_._wait_condition.wait_for(lambda: self_._is_interrupted(), timeout=self_.last_backoff_time)
                    except Exception:
                        logger.error('Unexpected error occurred in Neptune background thread: %s', self.kill_message)
                        raise
                return None
            return wrapper