from __future__ import annotations
__all__ = ['get_backend']
from typing import TYPE_CHECKING
from minfx.neptune_v2.exceptions import AllBackendsFailedError, BackendError
from minfx.neptune_v2.internal.backends.backend_config import BackendConfig, configs_from_tokens
from minfx.neptune_v2.internal.credentials import Credentials
from minfx.neptune_v2.internal.utils.logger import get_logger
from minfx.neptune_v2.types.mode import Mode
from .hosted_neptune_backend import HostedNeptuneBackend
from .multi_backend import MultiBackend
from .neptune_backend_mock import NeptuneBackendMock
from .offline_neptune_backend import OfflineNeptuneBackend
logger = get_logger()

def get_backend(mode, backends=None, proxies=None):
    if mode == Mode.DEBUG:
        return NeptuneBackendMock()
    if mode == Mode.OFFLINE:
        return OfflineNeptuneBackend()
    if backends is None:
        backends = configs_from_tokens(None, proxies=proxies)
    return _get_backend_from_configs(mode=mode, configs=backends, proxies=proxies)

def _get_backend_from_configs(mode, configs, proxies=None):
    if not configs:
        raise ValueError('At least one backend configuration is required')
    total_backends = len(configs)
    is_multi = total_backends > 1
    if is_multi:
        logger.info(f'Connecting to {total_backends} backends...')
    backends = []
    creation_errors = []
    for index, config in enumerate(configs):
        effective_proxies = config.proxies or proxies
        role_marker = '(primary)' if index == 0 else '(secondary)'
        backend_url = _get_url_from_token(config.api_token)
        if is_multi:
            logger.info(f'[backend {index}] ({backend_url}): connecting {role_marker}...')
        try:
            backend = _create_single_backend(mode=mode, api_token=config.api_token, proxies=effective_proxies, project_name_override=config.project, backend_index=index)
            backends.append((index, backend))
            if is_multi:
                logger.info(f'[backend {index}] ({backend.get_display_address()}): connected {role_marker}')
        except Exception as e:
            if is_multi:
                error_type = type(e).__name__
                logger.warning(f'[backend {index}] ({backend_url}): failed to connect {role_marker} - {error_type}: {e}')
                creation_errors.append(BackendError(backend_index=index, cause=e))
            else:
                raise
    if not backends:
        raise AllBackendsFailedError(creation_errors)
    if is_multi:
        if creation_errors:
            logger.warning(f'Backend connection completed: {len(backends)}/{total_backends} backends ready')
        else:
            logger.info(f'Backend connection completed: {len(backends)}/{total_backends} backends ready')
    return MultiBackend.from_indexed_backends(backends)

def _get_url_from_token(api_token):
    if api_token is None:
        return 'unknown'
    try:
        creds = Credentials.from_token(api_token)
        return creds.token_origin_address
    except Exception:
        return 'unknown'

def _create_single_backend(mode, api_token=None, proxies=None, project_name_override=None, backend_index=None):
    if mode in (Mode.ASYNC, Mode.SYNC, Mode.READ_ONLY):
        return HostedNeptuneBackend(credentials=Credentials.from_token(api_token=api_token), proxies=proxies, project_name_override=project_name_override, backend_index=backend_index)
    if mode == Mode.DEBUG:
        return NeptuneBackendMock()
    if mode == Mode.OFFLINE:
        return OfflineNeptuneBackend()
    raise ValueError(f'mode should be one of {list(Mode)}')