from __future__ import annotations
__all__ = ['load_extensions']
from importlib.metadata import entry_points
import sys
from typing import Callable
from minfx.neptune_v2.common.warnings import NeptuneWarning, warn_once

def get_entry_points(name):
    if (3, 8) <= sys.version_info < (3, 10):
        return [(entry_point.name, entry_point.load()) for entry_point in entry_points().get(name, ())]
    return [(entry_point.name, entry_point.load()) for entry_point in entry_points(group=name)]

def load_extensions():
    for entry_point_name, loaded_extension in get_entry_points(name='neptune.extensions'):
        try:
            _ = loaded_extension()
        except Exception as e:
            warn_once(message=f'Failed to load neptune extension `{entry_point_name}` with exception: {e}', exception=NeptuneWarning)