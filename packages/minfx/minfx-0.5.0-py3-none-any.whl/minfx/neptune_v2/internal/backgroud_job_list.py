from __future__ import annotations
__all__ = ['BackgroundJobList']
import time
from typing import TYPE_CHECKING
from minfx.neptune_v2.internal.background_job import BackgroundJob

class BackgroundJobList(BackgroundJob):

    def __init__(self, jobs):
        self._jobs = jobs

    def start(self, container):
        for job in self._jobs:
            job.start(container)

    def stop(self):
        for job in self._jobs:
            job.stop()

    def join(self, seconds=None):
        ts = time.time()
        for job in self._jobs:
            sec_left = None if seconds is None else seconds - (time.time() - ts)
            job.join(sec_left)

    def pause(self):
        for job in self._jobs:
            job.pause()

    def resume(self):
        for job in self._jobs:
            job.resume()