__all__ = ('ReadOnlyOperationProcessor',)
from typing import TYPE_CHECKING
from minfx.neptune_v2.common.warnings import NeptuneWarning, warn_once
from minfx.neptune_v2.internal.operation_processors.operation_processor import OperationProcessor

class ReadOnlyOperationProcessor(OperationProcessor):

    def enqueue_operation(self, op, *, wait):
        warn_once('Client in read-only mode, nothing will be saved to server.', exception=NeptuneWarning)