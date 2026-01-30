from __future__ import annotations
__all__ = ['AltairChartLike', 'BokehFigureLike', 'MatplotlibAxesLike', 'MatplotlibFigureLike', 'NumpyArrayLike', 'PILImageLike', 'PlotlyFigureLike', 'SeabornGridLike', 'TensorflowTensorLike', 'TorchTensorLike']
from typing import TYPE_CHECKING, Protocol, runtime_checkable

@runtime_checkable
class NumpyArrayLike(Protocol):

    @property
    def shape(self):
        ...

    def copy(self):
        ...

    def min(self):
        ...

    def max(self):
        ...

    def astype(self, dtype):
        ...

@runtime_checkable
class PILImageLike(Protocol):

    def save(self, fp, format=None):
        ...

@runtime_checkable
class MatplotlibFigureLike(Protocol):

    def savefig(self, fname, *, format=None, bbox_inches=None):
        ...

@runtime_checkable
class MatplotlibAxesLike(Protocol):

    @property
    def figure(self):
        ...

@runtime_checkable
class PlotlyFigureLike(Protocol):

    def write_html(self, file, *, include_plotlyjs=True):
        ...

@runtime_checkable
class AltairChartLike(Protocol):

    def save(self, fp, format=None):
        ...

@runtime_checkable
class BokehFigureLike(Protocol):
    pass

@runtime_checkable
class SeabornGridLike(Protocol):

    @property
    def figure(self):
        ...

@runtime_checkable
class TorchTensorLike(Protocol):

    def detach(self):
        ...

    def numpy(self):
        ...

@runtime_checkable
class TensorflowTensorLike(Protocol):

    def numpy(self):
        ...