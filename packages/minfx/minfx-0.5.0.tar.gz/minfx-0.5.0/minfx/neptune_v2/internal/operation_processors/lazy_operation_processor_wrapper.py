from __future__ import annotations
__all__ = ('LazyOperationProcessorWrapper',)
from typing import TYPE_CHECKING, Any, Callable, TypeVar
from minfx.neptune_v2.core.components.abstract import Resource
from minfx.neptune_v2.internal.operation_processors.operation_processor import OperationProcessor
RT = TypeVar('RT')

def trigger_evaluation(method):

    def _wrapper(self, *args, **kwargs):
        self.evaluate()
        return method(self, *args, **kwargs)
    return _wrapper

def noop_if_not_evaluated(method):

    def _wrapper(self, *args, **kwargs):
        if self.is_evaluated:
            return method(self, *args, **kwargs)
        return None
    return _wrapper

def noop_if_evaluated(method):

    def _wrapper(self, *args, **kwargs):
        if not self.is_evaluated:
            return method(self, *args, **kwargs)
        return None
    return _wrapper

class LazyOperationProcessorWrapper(OperationProcessor):

    def __init__(self, operation_processor_getter, post_trigger_side_effect=None):
        self._operation_processor_getter = operation_processor_getter
        self._post_trigger_side_effect = post_trigger_side_effect
        self._operation_processor = None

    @noop_if_evaluated
    def evaluate(self):
        self._operation_processor = self._operation_processor_getter()
        self._operation_processor.start()

    @property
    def is_evaluated(self):
        return self._operation_processor is not None

    @trigger_evaluation
    def enqueue_operation(self, op, *, wait):
        self._operation_processor.enqueue_operation(op, wait=wait)

    @property
    @trigger_evaluation
    def operation_storage(self):
        return self._operation_processor.operation_storage

    @property
    @trigger_evaluation
    def data_path(self):
        if isinstance(self._operation_processor, Resource):
            return self._operation_processor.data_path
        raise NotImplementedError

    @trigger_evaluation
    def start(self):
        self._operation_processor.start()

    @noop_if_not_evaluated
    def pause(self):
        self._operation_processor.pause()

    @noop_if_not_evaluated
    def resume(self):
        self._operation_processor.resume()

    @noop_if_not_evaluated
    def flush(self):
        self._operation_processor.flush()

    @noop_if_not_evaluated
    def wait(self):
        self._operation_processor.wait()

    @noop_if_not_evaluated
    def stop(self, seconds=None):
        self._operation_processor.stop(seconds=seconds)

    @noop_if_not_evaluated
    def close(self):
        self._operation_processor.close()