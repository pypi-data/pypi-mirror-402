from __future__ import annotations
__all__ = ['project_name_lookup']
import os
from typing import TYPE_CHECKING
from minfx.neptune_v2.envs import PROJECT_ENV_NAME
from minfx.neptune_v2.exceptions import NeptuneMissingProjectNameException
from minfx.neptune_v2.internal.utils import verify_type
from minfx.neptune_v2.internal.utils.logger import get_logger
_logger = get_logger()

def project_name_lookup(backend, name=None):
    verify_type('name', name, (str, type(None)))
    if not name:
        name = os.getenv(PROJECT_ENV_NAME)
    if not name:
        available_workspaces = backend.get_available_workspaces()
        available_projects = backend.get_available_projects()
        raise NeptuneMissingProjectNameException(available_workspaces=available_workspaces, available_projects=available_projects)
    return backend.get_project(name)