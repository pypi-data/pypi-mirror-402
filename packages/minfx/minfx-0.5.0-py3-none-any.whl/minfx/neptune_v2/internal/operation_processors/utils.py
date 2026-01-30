from __future__ import annotations
__all__ = ['common_metadata', 'get_container_dir', 'get_container_full_path']
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import random
import string
import sys
from typing import TYPE_CHECKING, Any
from minfx.neptune_v2.constants import NEPTUNE_DATA_DIRECTORY
from minfx.neptune_v2.metadata_containers.structure_version import StructureVersion
RANDOM_KEY_LENGTH = 8

def get_neptune_version():
    from minfx.neptune_v2.version import __version__ as neptune_version
    return neptune_version

def common_metadata(mode, container_id, container_type):
    return {'mode': mode, 'containerId': container_id, 'containerType': container_type, 'structureVersion': StructureVersion.DIRECT_DIRECTORY.value, 'os': platform.platform(), 'pythonVersion': sys.version, 'neptuneClientVersion': get_neptune_version(), 'createdAt': datetime.now(timezone.utc).isoformat()}

def get_container_dir(container_id, container_type):
    return f'{container_type.value}__{container_id}__{os.getpid()}__{random_key(RANDOM_KEY_LENGTH)}'

def get_container_full_path(type_dir, container_id, container_type):
    neptune_data_dir = Path(os.getenv('NEPTUNE_DATA_DIRECTORY', NEPTUNE_DATA_DIRECTORY))
    return neptune_data_dir / type_dir / get_container_dir(container_id=container_id, container_type=container_type)

def random_key(length):
    characters = string.ascii_lowercase + string.digits
    return ''.join((random.choice(characters) for _ in range(length)))