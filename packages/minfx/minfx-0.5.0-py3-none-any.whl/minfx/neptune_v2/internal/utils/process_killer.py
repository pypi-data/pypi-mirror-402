from __future__ import annotations
__all__ = ['kill_me']
import contextlib
import os
import signal
from minfx.neptune_v2.envs import NEPTUNE_SUBPROCESS_KILL_TIMEOUT
try:
    import psutil
    PSUTIL_INSTALLED = True
except ImportError:
    PSUTIL_INSTALLED = False
KILL_TIMEOUT = int(os.getenv(NEPTUNE_SUBPROCESS_KILL_TIMEOUT, '5'))

def kill_me():
    if PSUTIL_INSTALLED:
        process = psutil.Process(os.getpid())
        try:
            children = _get_process_children(process)
        except psutil.NoSuchProcess:
            children = []
        for child_proc in children:
            _terminate(child_proc)
        _, alive = psutil.wait_procs(children, timeout=KILL_TIMEOUT)
        for child_proc in alive:
            _kill(child_proc)
        _terminate(process)
    else:
        os.kill(os.getpid(), signal.SIGINT)

def _terminate(process):
    with contextlib.suppress(psutil.NoSuchProcess):
        process.terminate()

def _kill(process):
    try:
        if process.is_running():
            process.kill()
    except psutil.NoSuchProcess:
        pass

def _get_process_children(process):
    try:
        return process.children(recursive=True)
    except psutil.NoSuchProcess:
        return []