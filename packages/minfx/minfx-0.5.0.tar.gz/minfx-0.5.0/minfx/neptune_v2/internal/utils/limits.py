from __future__ import annotations
__all__ = ['custom_run_id_exceeds_length', 'image_size_exceeds_limit_for_logging']
import warnings
from minfx.neptune_v2.internal.utils.logger import get_logger
_logger = get_logger()
_CUSTOM_RUN_ID_LENGTH = 36
_LOGGED_IMAGE_SIZE_LIMIT_MB = 32
BYTES_IN_MB = 1024 * 1024

def custom_run_id_exceeds_length(custom_run_id):
    if custom_run_id and len(custom_run_id) > _CUSTOM_RUN_ID_LENGTH:
        _logger.warning('Given custom_run_id exceeds %s characters and it will be ignored.', _CUSTOM_RUN_ID_LENGTH)
        return True
    return False

def image_size_exceeds_limit_for_logging(content_size):
    if content_size > _LOGGED_IMAGE_SIZE_LIMIT_MB * BYTES_IN_MB:
        warnings.warn(f'You are attempting to log an image that is {content_size / BYTES_IN_MB:.2f}MB large. Neptune supports logging images smaller than {_LOGGED_IMAGE_SIZE_LIMIT_MB}MB. Resize or increase compression of this image.', stacklevel=2, category=UserWarning)
        return True
    return False