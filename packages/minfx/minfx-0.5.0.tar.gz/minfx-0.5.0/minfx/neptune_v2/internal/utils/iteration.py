from __future__ import annotations
__all__ = ['get_batches']
from itertools import chain, islice
from typing import Iterable, TypeVar
T = TypeVar('T')

def get_batches(iterable, *, batch_size):
    assert batch_size > 0
    source_iter = iter(iterable)
    while True:
        slices = islice(source_iter, batch_size)
        try:
            first_from_slice = next(slices)
        except StopIteration:
            return
        yield list(chain([first_from_slice], slices))