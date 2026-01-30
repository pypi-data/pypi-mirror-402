from __future__ import annotations
from typing import Any
__all__ = ['ExecuteOperationsBatchingManager', 'MissingApiClient', 'NeptuneResponseAdapter', 'build_operation_url', 'cache', 'construct_progress_bar', 'create_swagger_client', 'handle_server_raw_response_messages', 'parse_validation_errors', 'ssl_verify', 'update_session_proxies', 'verify_client_version', 'verify_host_resolution', 'which_progress_bar']
import dataclasses
from functools import lru_cache, wraps
import os
import socket
from typing import TYPE_CHECKING, Callable, Iterable, Mapping, ParamSpec, TypeVar
P = ParamSpec('P')
T = TypeVar('T')
from urllib.parse import urljoin, urlparse
from bravado.client import SwaggerClient
from bravado.requests_client import RequestsResponseAdapter
from bravado_core.formatter import SwaggerFormat
from packaging.version import Version
import urllib3
from minfx.neptune_v2.common.backends.utils import with_api_exceptions_handler
from minfx.neptune_v2.common.warnings import NeptuneWarning, warn_once
from minfx.neptune_v2.envs import NEPTUNE_ALLOW_SELF_SIGNED_CERTIFICATE
from minfx.neptune_v2.exceptions import CannotResolveHostname, MetadataInconsistency, NeptuneClientUpgradeRequiredError, NeptuneFeatureNotAvailableException
from minfx.neptune_v2.internal.backends.swagger_client_wrapper import SwaggerClientWrapper
from minfx.neptune_v2.internal.operation import CopyAttribute, Operation
from minfx.neptune_v2.internal.utils import replace_patch_version
from minfx.neptune_v2.internal.utils.logger import get_logger
from minfx.neptune_v2.progress_bar import NullProgressBar, ProgressBarCallback, ProgressBarType, TqdmProgressBar
logger = get_logger()

@lru_cache(maxsize=None, typed=True)
def verify_host_resolution(url):
    host = urlparse(url).netloc.split(':')[0]
    try:
        socket.gethostbyname(host)
    except socket.gaierror:
        raise CannotResolveHostname(host)
uuid_format = SwaggerFormat(format='uuid', to_python=lambda x: x, to_wire=lambda x: x, validate=lambda x: None, description='')

@with_api_exceptions_handler
def create_swagger_client(url, http_client, backend_index=None):
    _ = backend_index
    response = http_client.session.get(url)
    response.raise_for_status()
    spec_dict = response.json()
    spec_dict.pop('host', None)
    parsed = urlparse(url)
    origin_url = f'{parsed.scheme}://{parsed.netloc}'
    return SwaggerClient.from_spec(spec_dict, origin_url=origin_url, http_client=http_client, config={'validate_swagger_spec': False, 'validate_requests': False, 'validate_responses': False, 'formats': [uuid_format]})

def verify_client_version(client_config, version):
    version_with_patch_0 = Version(replace_patch_version(str(version)))
    if client_config.version_info.min_compatible and client_config.version_info.min_compatible > version:
        raise NeptuneClientUpgradeRequiredError(version, min_version=client_config.version_info.min_compatible)
    if client_config.version_info.max_compatible and client_config.version_info.max_compatible < version_with_patch_0:
        raise NeptuneClientUpgradeRequiredError(version, max_version=client_config.version_info.max_compatible)
    if client_config.version_info.min_recommended and client_config.version_info.min_recommended > version:
        logger.warning('WARNING: Your version of the Neptune client library (%s) is deprecated, and soon will no longer be supported by the Neptune server. We recommend upgrading to at least version %s.', version, client_config.version_info.min_recommended)

def update_session_proxies(session, proxies):
    if proxies:
        try:
            session.proxies.update(proxies)
        except (TypeError, ValueError):
            raise ValueError(f'Wrong proxies format: {proxies}')

def build_operation_url(base_api, operation_url):
    if '://' not in base_api:
        base_api = f'https://{base_api}'
    return urljoin(base=base_api, url=operation_url)

def handle_server_raw_response_messages(response):
    try:
        info = response.headers.get('X-Server-Info')
        if info:
            logger.info(info)
        warning = response.headers.get('X-Server-Warning')
        if warning:
            logger.warning(warning)
        error = response.headers.get('X-Server-Error')
        if error:
            logger.error(error)
        return response
    except Exception:
        return response

class NeptuneResponseAdapter(RequestsResponseAdapter):

    @property
    def raw_bytes(self):
        self._handle_response()
        return super().raw_bytes

    @property
    def text(self):
        self._handle_response()
        return super().text

    def json(self, **kwargs):
        self._handle_response()
        return super().json(**kwargs)

    def _handle_response(self):
        try:
            info = self._delegate.headers.get('X-Server-Info')
            if info:
                logger.info(info)
            warning = self._delegate.headers.get('X-Server-Warning')
            if warning:
                logger.warning(warning)
            error = self._delegate.headers.get('X-Server-Error')
            if error:
                logger.error(error)
        except Exception:
            pass

class MissingApiClient(SwaggerClientWrapper):

    def __init__(self, feature_name):
        self.feature_name = feature_name

    def __getattr__(self, item):
        raise NeptuneFeatureNotAvailableException(missing_feature=self.feature_name)

def cache(func):

    class HDict(dict):

        def __hash__(self):
            return hash(frozenset(self.items()))
    func = lru_cache(maxsize=None, typed=True)(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        args = tuple([HDict(arg) if isinstance(arg, dict) else arg for arg in args])
        kwargs = {k: HDict(v) if isinstance(v, dict) else v for k, v in kwargs.items()}
        return func(*args, **kwargs)
    wrapper.cache_clear = func.cache_clear
    return wrapper

def ssl_verify():
    if os.getenv(NEPTUNE_ALLOW_SELF_SIGNED_CERTIFICATE):
        urllib3.disable_warnings()
        return False
    return True

def parse_validation_errors(error):
    return {f"{error_description.get('errorCode').get('name')}": error_description.get('context', '') for validation_error in error.swagger_result.validationErrors for error_description in validation_error.get('errors')}

@dataclasses.dataclass
class OperationsBatch:
    operations: list[Operation] = dataclasses.field(default_factory=list)
    errors: list[MetadataInconsistency] = dataclasses.field(default_factory=list)
    dropped_operations_count: int = 0

class ExecuteOperationsBatchingManager:

    def __init__(self, backend):
        self._backend = backend

    def get_batch(self, ops):
        result = OperationsBatch()
        for op in ops:
            if isinstance(op, CopyAttribute):
                if not result.operations:
                    try:
                        result.operations.append(op.resolve(self._backend))
                    except MetadataInconsistency as e:
                        result.errors.append(e)
                        result.dropped_operations_count += 1
                else:
                    break
            else:
                result.operations.append(op)
        return result

def _check_if_tqdm_installed():
    try:
        import tqdm
        return True
    except ImportError:
        return False

def which_progress_bar(progress_bar):
    if isinstance(progress_bar, type) and issubclass(progress_bar, ProgressBarCallback):
        return progress_bar
    if not isinstance(progress_bar, bool) and progress_bar is not None:
        raise TypeError(f'progress_bar should be None, bool or ProgressBarCallback, got {type(progress_bar).__name__}')
    if progress_bar or progress_bar is None:
        tqdm_available = _check_if_tqdm_installed()
        if not tqdm_available:
            warn_once('To use the default progress bar, please install tqdm: pip install tqdm', exception=NeptuneWarning)
            return NullProgressBar
        return TqdmProgressBar
    return NullProgressBar

def construct_progress_bar(progress_bar, description):
    progress_bar_type = which_progress_bar(progress_bar)
    return progress_bar_type(description=description)