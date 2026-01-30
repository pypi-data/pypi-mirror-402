__all__ = ['BatchLagSignal', 'BatchProcessedSignal', 'BatchStartedSignal', 'Signal', 'SignalsVisitor']
from abc import abstractmethod
from dataclasses import dataclass

@dataclass
class Signal:
    occured_at: float

    @abstractmethod
    def accept(self, visitor):
        ...

@dataclass
class BatchStartedSignal(Signal):

    def accept(self, visitor):
        visitor.visit_batch_started(signal=self)

@dataclass
class BatchProcessedSignal(Signal):

    def accept(self, visitor):
        visitor.visit_batch_processed(signal=self)

@dataclass
class BatchLagSignal(Signal):
    lag: float

    def accept(self, visitor):
        visitor.visit_batch_lag(signal=self)

class SignalsVisitor:

    @abstractmethod
    def visit_batch_started(self, signal):
        ...

    @abstractmethod
    def visit_batch_processed(self, signal):
        ...

    @abstractmethod
    def visit_batch_lag(self, signal):
        ...