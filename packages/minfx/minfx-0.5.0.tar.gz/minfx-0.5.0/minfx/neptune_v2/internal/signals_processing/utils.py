from __future__ import annotations
__all__ = ['signal_batch_lag', 'signal_batch_processed', 'signal_batch_started']
from queue import Full, Queue
from time import monotonic
from minfx.neptune_v2.common.warnings import NeptuneWarning, warn_once
from minfx.neptune_v2.internal.signals_processing.signals import BatchLagSignal, BatchProcessedSignal, BatchStartedSignal, Signal

def signal(*, queue, obj):
    try:
        queue.put_nowait(item=obj)
    except Full:
        warn_once('Signal queue is full. Some signals will be lost.', exception=NeptuneWarning)

def signal_batch_started(*, queue, occured_at=None):
    signal(queue=queue, obj=BatchStartedSignal(occured_at=occured_at or monotonic()))

def signal_batch_processed(*, queue, occured_at=None):
    signal(queue=queue, obj=BatchProcessedSignal(occured_at=occured_at or monotonic()))

def signal_batch_lag(*, queue, lag, occured_at=None):
    signal(queue=queue, obj=BatchLagSignal(occured_at=occured_at or monotonic(), lag=lag))