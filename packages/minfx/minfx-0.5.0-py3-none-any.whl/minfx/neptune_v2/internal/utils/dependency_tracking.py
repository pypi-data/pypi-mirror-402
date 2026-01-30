from __future__ import annotations
__all__ = ['DependencyTrackingStrategy', 'FileDependenciesStrategy', 'InferDependenciesStrategy']
from abc import ABC, abstractmethod
from importlib.metadata import Distribution, distributions
import os
from pathlib import Path
from typing import TYPE_CHECKING
from minfx.neptune_v2.internal.utils.logger import get_logger
from minfx.neptune_v2.types import File
logger = get_logger()

class DependencyTrackingStrategy(ABC):

    @abstractmethod
    def log_dependencies(self, run):
        ...

class InferDependenciesStrategy(DependencyTrackingStrategy):

    def log_dependencies(self, run):
        dependencies = []

        def sorting_key_func(d):
            _name = d.metadata['Name']
            return _name.lower() if isinstance(_name, str) else ''
        dists = sorted(distributions(), key=sorting_key_func)
        for dist in dists:
            if dist.metadata['Name']:
                dependencies.append(f"{dist.metadata['Name']}=={dist.metadata['Version']}")
        dependencies_str = '\n'.join(dependencies)
        if dependencies_str:
            run['source_code/requirements'].upload(File.from_content(dependencies_str))

class FileDependenciesStrategy(DependencyTrackingStrategy):

    def __init__(self, path):
        self._path = path

    def log_dependencies(self, run):
        if Path(self._path).is_file():
            run['source_code/requirements'].upload(self._path)
        else:
            logger.warning("File '%s' does not exist - skipping dependency file upload.", self._path)