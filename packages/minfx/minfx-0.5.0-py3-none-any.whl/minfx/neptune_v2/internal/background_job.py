from __future__ import annotations
__all__ = ['BackgroundJob']
import abc
from typing import TYPE_CHECKING

class BackgroundJob:

    @abc.abstractmethod
    def start(self, container):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def join(self, seconds=None):
        pass

    @abc.abstractmethod
    def pause(self):
        pass

    @abc.abstractmethod
    def resume(self):
        pass