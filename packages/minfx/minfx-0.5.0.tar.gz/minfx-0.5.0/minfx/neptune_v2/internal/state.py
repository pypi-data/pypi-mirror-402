__all__ = ['ContainerState', 'ForkingState', 'OperationAcceptance']
from enum import Enum

class ContainerState(Enum):
    CREATED = 'created'
    STARTED = 'started'
    STOPPING = 'stopping'
    STOPPED = 'stopped'

class ForkingState(Enum):
    IDLE = 'idle'
    FORKING = 'forking'

    def is_forking(self):
        return self == ForkingState.FORKING

class OperationAcceptance(Enum):
    ACCEPTING = 'accepting'
    REJECTING = 'rejecting'

    def is_accepting(self):
        return self == OperationAcceptance.ACCEPTING