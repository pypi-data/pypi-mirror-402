from __future__ import annotations
__all__ = ['create_checkpoint']
import threading
from typing import TYPE_CHECKING
from minfx.neptune_v2.internal.notebooks.comm import send_checkpoint_created
from minfx.neptune_v2.internal.utils import is_ipython
from minfx.neptune_v2.internal.utils.logger import get_logger
_logger = get_logger()
_checkpoints_lock = threading.Lock()
_checkpoints = {}

def create_checkpoint(backend, notebook_id, notebook_path):
    if is_ipython():
        import IPython
        ipython = IPython.core.getipython.get_ipython()
        execution_count = -1
        if ipython.kernel is not None:
            execution_count = ipython.kernel.execution_count
        with _checkpoints_lock:
            if execution_count in _checkpoints:
                return _checkpoints[execution_count]
            checkpoint = backend.create_checkpoint(notebook_id, notebook_path)
            if ipython is not None and ipython.kernel is not None:
                send_checkpoint_created(notebook_id=notebook_id, notebook_path=notebook_path, checkpoint_id=checkpoint)
                _checkpoints[execution_count] = checkpoint
            return checkpoint
    return None