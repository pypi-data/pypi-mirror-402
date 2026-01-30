from __future__ import annotations
__all__ = ('OperationProcessor',)
import abc
from typing import TYPE_CHECKING

class OperationProcessor(abc.ABC):

    @abc.abstractmethod
    def enqueue_operation(self, op, *, wait):
        ...

    @property
    def operation_storage(self):
        raise NotImplementedError

    def start(self):
        pass

    def pause(self):
        pass

    def resume(self):
        pass

    def flush(self):
        pass

    def wait(self):
        pass

    def stop(self, seconds=None):
        pass

    def close(self):
        pass